def main() -> None:
    try:
        from sierra_agent.agent import SierraAgent

        agent = SierraAgent()
    except RuntimeError as exc:
        print(f"Setup needed: {exc}")
        return

    print("Sierra Outfitters agent ready. Type 'exit' or 'quit' to leave the trail.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOnward into the unknown. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Onward into the unknown. Goodbye!")
            break

        try:
            response = agent.respond(user_input)
        except RuntimeError as exc:
            response = f"I hit a snag on the trail: {exc}"

        print(f"\nSierra: {response}")


if __name__ == "__main__":
    main()
