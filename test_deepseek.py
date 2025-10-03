from deepseek import ask_deepseek

if __name__ == "__main__":
    question = "What is the capital of France?"
    answer = ask_deepseek(question)
    print("DeepSeek Answer:", answer)