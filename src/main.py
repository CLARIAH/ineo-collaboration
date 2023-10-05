import harvester
import template
import ineo_sync
import logging

# TODO: call harvester
def call_harvester():
    harvester.main()
    logging.info("Harvester called")


# TODO: call template
def call_template():
    template.main()


# TODO: call ineo_sync
def call_ineo_sync():
    ineo_sync.main()


if "__main__" == __name__:
    call_harvester()
    call_template()
    call_ineo_sync()
    logging.info("All done")