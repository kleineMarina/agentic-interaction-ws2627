import sys
import agent.config as cf
import agent.run_log as rl
import agent.llm as llm
import time


def read_user_input():
    return ' '.join(sys.argv[1:]).strip()

def main():
    question = read_user_input()
    if not question:
        sys.exit('Usage: python -m agent "your question"')
    config = cf.load_config()
    logger = rl.RunLogger(config.MODEL)
    start = time.perf_counter()
    try:
        answer = llm.run_agent(question, config, logger)
        print(answer)

    except Exception as e:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.log('error', ok=False, duration_ms=duration_ms,
                   error=f'{type(e).__name__}: {e}')
        print('error: ', e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()