"""Agent loop: model -> tools -> model, until a final answer or the step limit."""

import json
import time
from datetime import date

from openai import OpenAI, BadRequestError

from agent.tools import CALENDAR_TOOL, get_calendar_day

SYSTEM_PROMPT = (
    'You are a calendar assistant. Use the tool get_calendar_day to look up '
    'appointments and never make up appointments. If the tool finds no data '
    'for a day, say so. '
    'If the tool returns an error, tell the user that the calendar could not '
    'be read for that day; never treat an error as "no appointments". '
    'Answer in the language of the question. '
    'Answer in plain text without Markdown tables. '
    'Today is {today}. '
)

MAX_STEPS = 10


def run_tool(tool_call, config, logger):
    """Runs one tool call requested by the model and returns the result as a JSON string."""
    name = tool_call.function.name

    # The model may send invalid JSON as arguments: keep the raw text instead of crashing
    try: 
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        args = {'raw_arguments': tool_call.function.arguments}
    logger.log('tool_call', tool=name, args=args)

    event = 'tool_result'
    start = time.perf_counter()
    try:
        if name == 'get_calendar_day':
            result = get_calendar_day(args['date'], config.DATA_BASE_URL)
        else:
            result = {'error': f'unknown tool: {name}'}
    except Exception as e:
        event = 'error'
        result = {'error': str(e)}
    duration_ms = round((time.perf_counter() - start) * 1000)

    logger.log(event, tool=name, args=args, ok='error' not in result,
               duration_ms=duration_ms, error=result.get('error'))

    return json.dumps(result, ensure_ascii=False)
    

def run_agent(question, config, logger):
    """Agent loop: model -> tools -> model, until a final answer or the step limit."""
    start = time.perf_counter()
    logger.log('user_task', args={'task': question})

    client = OpenAI(base_url=config.OPENAI_BASE_URL, api_key=config.OPENAI_API_KEY)
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT.format(today=date.today().isoformat())},
        {'role': 'user', 'content': question},
    ]
  
    step_count = 0
    final_answer = None
    while step_count < MAX_STEPS and final_answer is None:
        # Each step: ask the model with everything so far
        model_ok = True
        try:
            response = client.chat.completions.create(
                model=config.MODEL, messages=messages, tools=[CALENDAR_TOOL]
            )
            message = response.choices[0].message
        except BadRequestError as e:
            if e.code != 'output_parse_failed':
                raise
            model_ok = False
            logger.log('error', ok=False,
                       error=f'step {step_count + 1}: model output could not be parsed, retrying')

        if model_ok: 
            if message.tool_calls:
                # the model's request has to be in the history so the results can be matched to it
                messages.append({
                    'role': 'assistant',
                    'content': message.content,
                    'tool_calls': [
                        {
                            'id': tool_call.id,
                            'type': 'function',
                            'function': {
                                'name': tool_call.function.name,
                                'arguments': tool_call.function.arguments,
                            },
                        }
                        for tool_call in message.tool_calls
                    ],
                })

                for tool_call in message.tool_calls:
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_call.id,
                        'content': run_tool(tool_call, config, logger),
                    })

            else:
                if message.content:
                    final_answer = message.content
                else:
                    # gpt-oss sometimes returns neither a tool call nor text: log it and retry this step
                    logger.log('error', ok=False,
                               error=f'step {step_count + 1}: model returned an empty reply, retrying')
        step_count += 1

    if final_answer is None:
        raise RuntimeError(f'step limit reached: no answer after {MAX_STEPS} steps')

    # Only reached with a real answer: empty replies are retried inside the loop
    duration_ms = round((time.perf_counter() - start) * 1000)
    logger.log('final', ok=True, duration_ms=duration_ms)

    return final_answer
