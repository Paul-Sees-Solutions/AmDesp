import json
import os
import pathlib
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pprint import pprint

from dateutil.parser import parse

from python.despatchbay.despatchbay_sdk import DespatchBaySDK
from python.utils_pss.utils_pss import toCamel, get_from_ods

CONFIG_ODS = r"C:\AmDesp\data\AmDespConfig.ods"
FIELD_CONFIG = 'FIELD_CONFIG'
line = '-' * 100

class Config:
    def __init__(self, ):
        self.config_ods = CONFIG_ODS

        class DespatchConfig:
            def __init__(self):
                # if ship_mode == "sand":
                #     self.api_user = os.getenv("DESPATCH_API_USER_SANDBOX")
                #     self.api_key = os.getenv("DESPATCH_API_KEY_SANDBOX")
                # else:
                self.api_user = os.getenv("DESPATCH_API_USER")
                self.api_key = os.getenv("DESPATCH_API_KEY")
                self.sender_id = "5536"  # should be env var?
                self.client = DespatchBaySDK(api_user=self.api_user, api_key=self.api_key)
                self.sender = self.client.sender(address_id=self.sender_id)
                self.courier_id = 8
                self.shipping_service_id = 101  ## parcelforce 24 - maybe make dynamic?

        class FieldsCnfg:
            def __init__(self, ods):
                self.export_fields = None
                field_config_dict = get_from_ods(ods, FIELD_CONFIG, 'list')
                for k, v in field_config_dict.items():
                    setattr(self, k, v)

        class PathsConfig:
            def __init__(self):
                self.root = pathlib.Path("/Amdesp")
                self.data_dir = pathlib.Path("/Amdesp/data/")
                self.label_dir = self.data_dir / "Parcelforce Labels"
                self.Json_File = self.data_dir.joinpath("AmShip.json")
                self.xml_file = self.data_dir.joinpath('AmShip.xml')
                self.log_file = self.data_dir.joinpath("AmLog.json")
                self.config_file = self.data_dir.joinpath("AmDespConfig.Ods")
                self.bin_dir = pathlib.Path("/Amdesp/bin/")
                self.pdf_to_print = self.bin_dir.joinpath("PDFtoPrinter.exe")
                pathlib.Path(self.data_dir / "Parcelforce Labels").mkdir(parents=True,
                                                                         exist_ok=True)  # make the labels dirs (and parents)

        self.fields = FieldsCnfg(CONFIG_ODS)
        self.paths = PathsConfig()
        self.dbay_cnfg = DespatchConfig()


CNFG = Config()


class ShippingApp:
    def __init__(self, ship_mode):  # make app
        if ship_mode == 'sand':
            CNFG.dbay_cnfg.api_user = os.getenv("DESPATCH_API_USER_SANDBOX")
            CNFG.dbay_cnfg.api_key = os.getenv("DESPATCH_API_KEY_SANDBOX")
        self.shipment = None
        self.client = CNFG.dbay_cnfg.client
        self.sender = CNFG.dbay_cnfg.sender

    # def xml_to_shipment(self):
    #     self.shipment = XmlShipmentObj()
    def xml_to_shipment(self):
        ship_dict = self.xml_to_ship_dict()
        parsed = ShipDictObject(ship_dict)
        self.shipment = Shipment(parsed)

    def queue_shipment(self):
        self.shipment.val_boxes()  # checks if there are boxes on the shipment, prompts input and confirmation
        self.shipment.val_dates()  # checks collection is available on the sending date
        self.shipment.val_address()  # queries DB address database
        self.shipment.check_address()  # queries DB address database, prompts user to confirm match or call amend_address()
        self.shipment.make_request()  # make a shipment request
        if self.shipment.queue():
            return True
        else:
            print(f"Shipment aborted")

    def xml_to_ship_dict(self):
        print("XML IMPORTER ACTIVATED")
        ship_dict = {}
        tree = ET.parse(CNFG.paths.xml_file)
        root = tree.getroot()
        fields = root[0][2]
        category = root[0][0].text

        for field in fields:
            k = field[0].text
            v = field[1].text
            if v:
                if "Number" in k:
                    v = v.replace(",", "")
                ship_dict.update({k: v})
        if category == "Hire":
            print("Xml is a hire record")
            customer = root[0][3].text  # debug
            ship_dict['id'] = ship_dict['Reference Number']

        elif category == "Customer":
            print("Xml is a customer record")
            customer = fields[0][1].text
            ship_dict['send Out Date'] = datetime.today().strftime(
                '%d/%m/%Y')  # datedebug sets customer shipment send date to a string of today formatted like hire
            ship_dict['delivery tel'] = ship_dict['Deliv Telephone']

        else:
            print("no customer found")
            print("ERROR NO CUSTOMER")
        ship_dict.update({'customer': customer})
        ship_dict = self.clean_xml(ship_dict)
        if 'boxes' not in ship_dict.keys():
            ship_dict['boxes'] = 0
        for k, v in ship_dict.items():
            if k == "sendOutDate":
                v = datetime.strptime(v, '%d/%m/%Y')  # datedebug
        print(f"Making shipment object from xml with {len(ship_dict)} fields")
        return ship_dict

    def clean_xml(self, dict) -> dict:
        newdict = {}
        if "Send Out Date" not in dict.keys():
            print("No date - added today")
            dict['Send Out Date'] = datetime.today().strftime('%d/%m/%Y')
        for k, v in dict.items():
            # k = unsanitise(k)
            k = toCamel(k)
            if "deliv" in k:
                if "delivery" not in k:
                    k = k.replace('deliv', 'delivery')

            if v:
                # v = unsanitise(v)
                if isinstance(v, list):
                    v = v[0]
                if v.isnumeric():
                    v = int(v)
                    if v == 0:
                        v = None
                elif v.isalnum():
                    v = v.title()
                if 'Price' in k:
                    v = float(v)
                # if "Number" in k: # elsewhere?
                #     v = v.replace(",", "")
                # if k == "sendOutDate":
                # v = datetime.strftime(v, '%Y-%m-%d')   #debug wtf?
                # # v = datetime.strptime(v, '%Y%m-%d').date()
                # v = datetime.strptime(v, '%d/%m/%Y').date()

            newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        return newdict

    def book_collection(self):
        self.shipment.book_collection_()

    def log_json(self):
        # export from object attrs?
        export_dict = {}
        for field in CNFG.fields.export_fields:
            val = getattr(self.shipment, field)
            if isinstance(val, datetime):
                val = datetime.strftime(val, '%d-%m-%Y')
            export_dict.update({field: val})
        # if isinstance(export_dict, datetime):
        #     export_dict["sendOutDate"]=export_dict["sendOutDate"].strftime('%d/%m/%Y')
        # self.sendOutDate = self.sendOutDate.strftime('%d/%m/%Y')
        with open(CNFG.paths.log_file, 'a+') as f:
            json.dump(export_dict, f, sort_keys=True)
            pprint(f"\n Json exported to {CNFG.paths.log_file} {export_dict =}")


class Shipment:  # taking an xmlimporter object
    def __init__(self, parsed_xml_object, shipid=None,
                 shipref=None):  # shipdict is a hire object, could be a customer object, or repair i guess...
        self.sender = CNFG.dbay_cnfg.sender
        self.client = CNFG.dbay_cnfg.client
        self.collectionBooked = False
        self.dbAddressKey = 0
        self.dates = self.client.get_available_collection_dates(CNFG.dbay_cnfg.sender,
                                                                CNFG.dbay_cnfg.courier_id)  # get dates

        for field in CNFG.fields.shipment_fields:

            if field in vars(parsed_xml_object):
                v = getattr(parsed_xml_object, field)
                setattr(self, field, v)
            else:
                print(f"*** ERROR - {field} not found in ship_dict - ERROR ***")

        ## provided shipment details
        if shipid:
            self.id = shipid
        elif 'referenceNumber' in vars(parsed_xml_object):
            self.id = parsed_xml_object.referenceNumber
        else:
            self.id = "101"
        self.customer = parsed_xml_object.customer
        self.deliveryEmail = parsed_xml_object.deliveryEmail
        self.deliveryName = parsed_xml_object.deliveryName
        self.deliveryTel = parsed_xml_object.deliveryTel
        self.deliveryContact = parsed_xml_object.deliveryContact
        self.deliveryAddress = parsed_xml_object.deliveryAddress
        self.deliveryPostcode = parsed_xml_object.deliveryPostcode
        self.sendOutDate = parsed_xml_object.sendOutDate
        self.boxes = parsed_xml_object.boxes
        if shipref:
            self.shipRef = shipref  ## if there is a shipref passed use it as despatchbay reference on label etc
        else:
            self.shipRef = self.customer

        ## obtained shipment details
        self.deliveryBuildingNum = None
        self.deliveryFirstline = None
        self.shippingCost = None
        self.trackingNumbers = None
        self.labeLocation = None
        self.labelDownloaded = False
        self.labelLocation = None
        self.labelUrl = None
        self.parcels = None
        self.shipmentDocId = None
        self.shippingServiceName = None

        # DespatchBay Objects

        self.addedShipment = None
        self.addressObject = None
        self.dateObject = None
        self.shipmentRequest = None
        self.shipmentReturn = None
        self.recipient = None

        print("Shipment with id=", self.id, "created")

        def parse_address():
            print("--- Parsing Address...")
            crapstring = self.deliveryAddress
            firstline = crapstring.split("\n")[0]
            first_block = (crapstring.split(" ")[0]).split(",")[0]
            first_char = first_block[0]
            self.deliveryFirstline = firstline
            for char in firstline:
                if not char.isalnum() and char != " ":
                    firstline = firstline.replace(char, "")
            if first_char.isnumeric():
                self.deliveryBuildingNum = first_block

        def val_date_init(self):
            # dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
            if isinstance(self.sendOutDate, str):
                setattr(self, "sendOutDate", datetime.strptime(self.sendOutDate, '%d/%m/%Y'))
            for candidate in self.dates:
                if candidate.date == datetime.strftime(self.sendOutDate,
                                                       '%Y-%m-%d'):  # if date object matches send date
                    self.dateObject = candidate
                    print(line, '\n',
                          f"Shipment date for {self.customer} validated - {datetime.strftime(self.sendOutDate, '%A %B %#d')}")

        parse_address()
        val_date_init(self)

    def val_boxes(self):
        while True:
            if self.boxes:
                print(line, "\n",
                      f"\nShipment for {self.customer} has {self.boxes} box(es) assigned - is this correct?\n")
                ui = input(f"[C]onfirm or Enter a number of boxes\n")
                if ui.isnumeric():
                    self.boxes = int(ui)
                    print(f"Shipment updated  |  {self.boxes}  boxes\n")
                if ui == 'c':
                    print("Confirmed\n", line)
                    return self
                continue
            else:
                print("\n\t\t*** ERROR: No boxes added ***\n")
                ui = input(f"- How many boxes for shipment to {self.customer}?\n")
                if not ui.isnumeric():
                    print("- Enter a number")
                    continue
                self.boxes = int(ui)
                print(f"{self.customer} updated  |  ", self.boxes, "  boxes")
                # return self

    def val_dates(self):
        dates = self.client.get_available_collection_dates(CNFG.dbay_cnfg.sender,
                                                           CNFG.dbay_cnfg.courier_id)  # get dates
        print("--- Checking available collection dates...")
        send_date = datetime.strftime(self.sendOutDate, '%Y-%m-%d')

        for despdate in dates:
            compdate = str(despdate.date)
            if compdate == send_date:  # if date object matches send date
                self.dateObject = despdate
                da = datetime.strftime(self.sendOutDate, '%A %B %#d')
                print(f"Collection date match - shipment for {self.customer} will be collected on {da}\n", line)
                return
        else:  # loop exhausted, no date match
            print("\n*** ERROR: No collections available on", self.sendOutDate, "for",
                  self.customer, "***\n\n\n- Collections for", self.customer, "are available on:\n")
            for count, date in enumerate(dates):
                dt = parse(date.date)
                out = datetime.strftime(dt, '%A - %B %#d')
                print("\t\t", count + 1, "|", out)

            while True:
                choice = input('\n- Enter a number to choose a date, [0] to exit\n')
                if choice == "":
                    continue
                if not choice.isnumeric():
                    print("- Enter a number")
                    continue
                if not -1 <= int(choice) <= len(dates) + 1:
                    print('\nWrong Number!\n-Choose new date for', self.customer, '\n')
                    for count, date in enumerate(dates):
                        print("\t\t", count + 1, "|", date.date, )
                    continue
                if int(choice) == 0:
                    if input('[E]xit?')[0].lower() == "e":
                        exit()
                    continue
                else:
                    self.dateObject = dates[int(choice) - 1]
                    print("\t\tCollection date for", self.customer, "is now ", self.dateObject.date, "\n\n",
                          line)
                    return

    def val_address(self):
        if self.deliveryBuildingNum:
            if self.deliveryBuildingNum != 0:
                search_string = self.deliveryBuildingNum
            else:
                print("No building number, searching deliveryFirstline")
                self.deliveryBuildingNum = False
                search_string = self.deliveryFirstline
        else:
            print("No building number, searching deliveryFirstline")
            search_string = self.deliveryFirstline
        # get object
        try:
            address_object = self.client.find_address(self.deliveryPostcode, search_string)
        except:
            print("No address match found")
            self.change_address()
            return self
        else:
            self.addressObject = address_object
        return self

    def check_address(self):
        while True:
            if self.addressObject:
                ui = input(
                    f"\n- Recipient address is: \n{self.addressObject} \n- is this correct? \n[C]ontinue, anything else to change address\n\n")
                if ui[0].lower() == "c":
                    return
                else:
                    self.change_address()
            else:
                print("NO ADDRESS OBJECT")
                break

    def change_address(self, postcode=None):
        if postcode == None:
            postcode = self.deliveryPostcode
        candidates = self.client.get_address_keys_by_postcode(postcode)

        for count, candidate in enumerate(candidates, start=1):
            print(" - Candidate", str(count) + ":", candidate.address)
        selection = ""
        while True:
            selection = input('\n- Enter a candidate number, [0] to exit, [N] to search for a new address \n')
            if selection.isnumeric():
                selection = int(selection)
            else:
                if selection[0].lower() == "n":
                    if self.search_address():
                        return
                        # get address from postcode and number, or postcode and list
                    ...
                continue
            if selection == 0:
                if str(input("[e]xit?"))[0].lower() == "e":
                    return False
                    # exit()
                continue
            if not -1 <= selection <= len(candidates) + 1:
                print("Wrong Number")
                continue
            break
        selected_key = candidates[int(selection) - 1].key
        self.address_key = selected_key
        self.addressObject = self.client.get_address_by_key(selected_key)
        print(f"- New Address: {self.addressObject.company_name},{self.addressObject.street}")
        while True:
            ui = input("[A]mmend address, or [C]ontinue?")
            uii = ui[0].lower()
            if uii == "a":
                ...
            if uii == 'c':
                break
        return

    def search_address(self):
        pc = input("Enter postcode\n")
        ui = input("[L]ist addresses at postcode, or [E]nter a search term\n")
        if ui[0].lower() == 'l':
            self.change_address(pc)
            return
        elif ui[0].lower() == ['e']:
            s_string = input("Enter search string - number, or firstline, or business\n")

        else:
            self.search_address()
        try:
            address = self.client.find_address(pc, s_string)
        except:
            print("No results - try again\n")
            self.search_address()
        else:
            ui = ""
            while ui not in ['y', 'n']:
                ui = input(f"Is {address} correct? [Y]es or [N]o, or [E]xit\n")
                if ui[0].lower() == 'y':
                    self.addressObject = address
                    return
                elif ui[0].lower() == 'n':
                    self.search_address()
                elif ui[0].lower() == "e":
                    if input("really [E]xit?") == 'e':
                        exit()
                    self.search_address()

    def make_request(self):
        print("MAKING REQUEST")
        self.recipient_address = self.client.address(
            company_name=self.customer,
            country_code="GB",
            county=self.addressObject.county,
            locality=self.addressObject.locality,
            postal_code=self.addressObject.postal_code,
            town_city=self.addressObject.town_city,
            street=self.addressObject.street
        )

        self.recipient = self.client.recipient(
            name=self.deliveryContact,
            telephone=self.deliveryTel,
            email=self.deliveryEmail,
            recipient_address=self.recipient_address

        )
        self.parcels = []
        for x in range(self.boxes):
            parcel = self.client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            self.parcels.append(parcel)

        self.shipmentRequest = self.client.shipment_request(
            parcels=self.parcels,
            client_reference=self.shipRef,
            collection_date=self.dateObject.date,
            sender_address=self.sender,
            recipient_address=self.recipient,
            follow_shipment='true',
            service_id=101  # debug i added this manually?
        )
        self.shipmentRequest.collection_date = self.dateObject.date  #
        self.services = self.client.get_available_services(self.shipmentRequest)
        if self.services[0].service_id != CNFG.dbay_cnfg.shipping_service_id:
            print("Something is wrong with the shipping service name")
        self.shippingServiceName = self.services[0].name
        self.shippingCost = self.services[0].cost
        self.shipping_service_id = self.shipmentRequest.service_id
        self.services = self.services

    def queue(self):

        print("\n", line, '\n-', self.customer, "|", self.boxes, "|",
              self.addressObject.street, "|", self.dateObject.date, "|",
              self.shippingServiceName,
              "| Price =",
              self.shippingCost * self.boxes, '\n', line, '\n')
        choice = " "
        while True:
            choice = input('- [Q]ueue shipment in DespatchBay, [R]estart, or [E]xit\n')
            if choice:
                choice = str(choice[0].lower())
                if choice[0] != "q":  # not quote
                    if choice != 'r':  # not restart
                        if choice != 'e':  # not exit either
                            continue  # try again
                        else:  # exit
                            if str(input("[E]xit?"))[0].lower() == 'e':  # comfirn exit
                                break
                                # exit()
                            continue
                    else:  # restart
                        if str(input("[R]estart?"))[0].lower() == 'r':  # confirm restart
                            print("Restarting")
                        continue  # not restarting
                elif choice == 'q':
                    self.addedShipment = self.client.add_shipment(self.shipmentRequest)
                    print("Adding Shipment to Despatchbay Queue")
                    return True
            else:
                continue

    def book_collection(self):
        # CNFG = config
        print("[B]ook collection for", self.customer + "'s shipment?")
        while True:
            choice = input('- [B]ook, [R]estart, or [E]xit\n')
            choice = str(choice[0].lower())
            if choice[0] != "b":  # not book
                if choice != 'r':  # not restart
                    if choice != 'e':  # not exit either
                        continue  # try again
                    else:  # exit
                        if str(input("[E]xit?"))[0].lower() == 'e':  # comfirn exit
                            exit()
                        continue
                else:  # restart
                    if str(input("[R]estart?"))[0].lower() == 'r':  # confirm restart
                        print("Restarting")
                        ShippingApp.queue_shipment()  # debug does it run process? or soemthing else
                    continue  # not restarting
            elif choice == 'b':
                self.client.book_shipments(self.addedShipment)
                shipment_return = self.client.get_shipment(self.addedShipment)
                label_pdf = self.client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
                label_string = ""
                try:
                    label_string = label_string + self.customer + "-" + str(self.dateObject.date) + ".pdf"
                except:
                    label_string = label_string, self.customer, ".pdf"
                # label_pdf.download(CONFIG_PATH['DIR_LABEL'] / label_string)
                label_pdf.download(CNFG.paths.label_dir / label_string)
                self.trackingNumbers = []
                for parcel in shipment_return.parcels:
                    self.trackingNumbers.append(parcel.tracking_number)

                self.shipmentReturn = shipment_return
                self.shipmentDocId = shipment_return.shipment_document_id
                self.labelUrl = shipment_return.labels_url
                self.parcels = shipment_return.parcels
                self.labelLocation = str(CNFG.paths.label_dir / label_string)
                while True:
                    ui = input("[P]rint label or [E]xit?")
                    uii = ui[0].lower()
                    if uii == 'p':
                        command = (CNFG.paths.pdf_to_print, self.labelLocation)
                        subprocess.call(command, shell=True)
                    elif uii == 'e':
                        break
                self.collectionBooked = True
                self.labelDownloaded = True
                print(
                    f"\n Collection has been booked for {self.customer} on {self.dateObject.date} Label downloaded to {self.labelLocation}\n")
                return True


class ShipDictObject:
    def __init__(self, ship_dict):
        for k, v in ship_dict.items():
            setattr(self, k, v)
