"""The daily run: collect, check and build the history. Run once a day."""

import check
import table
from collect import collect, log


def main():
    log.info("step 1 of 3: the category pages")
    collect()
    log.info("step 2 of 3: check the collection")
    check.verify()
    log.info("step 3 of 3: the price history")
    table.write_csv(table.build())


if __name__ == "__main__":
    main()
