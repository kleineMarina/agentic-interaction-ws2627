"""Agent loop: model -> tool -> model."""

import json
import time
from datetime import date

from openai import OpenAI

from agent.tools import CALENDAR_TOOL, get_calendar_day

SYSTEM_PROMPT = (
    'You are a calendar assistant. Use the tool get_calendar_day to look up '
    'appointments and never make up appointments. If the tool finds no data '
    'for a day, say so. Answer in the language of the question. '
    'Answer in plain text without Markdown tables. '
    'Today is {today}. '
)


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
    """Answers a question: model -> tool -> model. Returns the final answer."""
    start = time.perf_counter()
    logger.log('user_task', args={'task': question})

    client = OpenAI(base_url=config.OPENAI_BASE_URL, api_key=config.OPENAI_API_KEY)
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT.format(today=date.today().isoformat())},
        {'role': 'user', 'content': question},
    ]

    # 1st model call: the model decides whether it needs the tool
    response = client.chat.completions.create(
        model=config.MODEL, messages=messages, tools=[CALENDAR_TOOL]
    )
    message = response.choices[0].message

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

        # 2nd model call: the model writes the answer from the tool results
        response = client.chat.completions.create(
            model=config.MODEL, messages=messages, tools=[CALENDAR_TOOL], tool_choice='none'
        )
        message = response.choices[0].message

    answer = message.content
    # The model may return no text: use a fallback answer and mark the run as not ok
    ok = bool(answer)
    if not ok:
        answer = 'Sorry, no answer could be generated.'
    duration_ms = round((time.perf_counter() - start) * 1000)
    logger.log('final', ok=ok, duration_ms=duration_ms,
               error=None if ok else 'model returned an empty answer')

    return answer
