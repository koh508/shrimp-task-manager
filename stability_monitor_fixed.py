import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    logging.info("Stability monitor started.")
    try:
        while True:
            logging.info("Monitoring system stability...")
            time.sleep(30)
    except KeyboardInterrupt:
        logging.info("Stability monitor stopped.")


if __name__ == "__main__":
    main()
