from python.AmDespProgrammer import ProgrammingAssistant
from python.AmDespShipper import ShippingApp

def shipper(ship_mode):
    app = ShippingApp(ship_mode)

    app.xml_to_shipment_()
    if app.queue_shipment_():
        if app.book_collection_():
            print("success")
    app.log_json()
    return "returned from python"


def programmer():
    prog = ProgrammingAssistant()
    prog.BootUp()
    prog.ProgramBatch()
    ...


def test():
    print("SOMETHNG")


if __name__ == '__main__':
    shipper('prod')
    # programmer()
    # test()