from groq_client import GroqClient

def main():
    client = GroqClient()

    while True:
        prompt = input("\nEnter your prompt (or type 'exit'): ")

        if prompt.lower() == "exit":
            break

        response = client.generate(prompt)
        print("\nResponse:\n", response)

if __name__ == "__main__":
    main()