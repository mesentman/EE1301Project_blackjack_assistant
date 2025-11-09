from dql_agent import train_and_export, train_and_export_test, train_and_export_quick
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        train_and_export_test()
    elif len(sys.argv) > 1 and sys.argv[1] == "quick":
        train_and_export_quick()
    else:
        train_and_export(num_episodes=500_000)
