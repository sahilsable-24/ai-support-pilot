import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.generation.llm_client import generate, LLMError


def main():
    prompt = "Explain what a refund policy is in two sentences."

    start = time.perf_counter()
    try:
        answer = generate(prompt)
    except LLMError as e:
        print(f"LLM error: {e}")
        return
    elapsed = time.perf_counter() - start

    print(answer)
    print(f"\nElapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()