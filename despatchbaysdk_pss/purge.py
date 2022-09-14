'''## temporarily removed expunging create shipment
# def submit_manifest(manifest):
#     for key, shipment in manifest.items():
#         print("\n" + shipment[customer_field] + "'s shipment of", shipment[boxes_field], "parcels to: ",
#               shipment[address_object_field].street, "|", shipment[date_object_field].date, "|",
#               shipment[shipping_service_name_field],
#               "| Price =",
#               shipment[shipping_cost_field])
#         if input('Type "yes" to book, other to skip shipment\n') == 'yes':
#             print("BOOKING SHIPMENT")
#
#             shipment_request.collection_date = shipment[date_object_field].date
#             added_shipment = client.add_shipment(shipment_request)
#             pprint(added_shipment)
#             shipment_return = client.get_shipment(added_shipment)
#             print("Added Shipment")
#             pprint (shipment_return)
#
#             # uncomment to book and get labels / tracking
#             # client.book_shipments([added_shipment])
#             # label_pdf = client.get_labels(shipment_return.shipment_document_id)
#             # label_string = 'data/parcelforce_labels/' + shipment['customer'] + "-" + shipment['collection_date'] + '.pdf'
#             # label_pdf.download(label_string)
#
#             shipment[is_shipped_field] = True
#
#             # records despatch references
#             # # format / print label ??
#
#
#
#         else:
#             print("Shipment", shipment[customer_field], "Skipped by User")
#             shipment[is_shipped_field] = False
#             continue
#
#     print("Datetime with out seconds", )
#
#     with open(logfile, 'w') as f:
#         new_out = {}
#         exclude_keys = [address_object_field, date_object_field, service_object_field]
#         for count, (key, shipment) in enumerate(manifest.items()):
#             output = {k: shipment[k] for k in set(list(shipment.keys())) - set(exclude_keys)}
#             date_blah = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
#             new_out.update({date_blah+" - "+shipment[customer_field]: output})
#             # print("dumped")
#         json.dump(new_out, f)
#
#     print("FINISHED")
#     if input("Restart?") == "yes":
#         book_shipments(manifest)
#     else:
#         exit()


# def create_shipment(shipment):
#     customer = shipment[customer_field]
#     phone = shipment[phone_field]
#     email = shipment[email_field]
#     address = shipment[address_object_field]
#     boxes = int(float(shipment[boxes_field]))
#     send_date = shipment[date_object_field]
#     recipient_name = shipment[delivery_contact_field]
#     recipient_address = client.address(
#         company_name=customer,
#         country_code="GB",
#         county=address.county,
#         locality=address.locality,
#         postal_code=address.postal_code,
#         town_city=address.town_city,
#         street=address.street
#     )
#
#     recipient = client.recipient(
#         name=recipient_name,
#         telephone=phone,
#         email=email,
#         recipient_address=recipient_address
#
#     )
#     parcels = []
#     for x in range(boxes):
#         parcel = client.parcel(
#             contents="Radios",
#             value=500,
#             weight=6,
#             length=60,
#             width=40,
#             height=40,
#         )
#         parcels.append(parcel)
#
#     shipment_request = client.shipment_request(
#         parcels=parcels,
#         client_reference=customer,
#         collection_date=send_date,
#         sender_address=sender,
#         recipient_address=recipient,
#         follow_shipment='true'
#     )
#     services = client.get_available_services(shipment_request)
#     shipment_request.service_id = services[0].service_id
#     shipment[shipping_service_name_field] = services[0].name
#     shipment[shipping_service_id_field] = shipment_request.service_id
#     shipment[shipping_cost_field] = services[0].cost


#### end of
'''


# def get_manifest_date_objects(manifest):
#     dates = client.get_available_collection_dates(sender, courier_id)
#     for count, shipment in enumerate(manifest):
#         ship_count = count
#         print(len(manifest))
#         print("Shipment", count + 1, "-", shipment[customer_field])
#         # # reverse send date and get matching collection dates
#         send_date_reversed = shipment[send_date_field].split("/")
#         send_date_reversed.reverse()
#         shipment[send_date_field] = '-'.join(send_date_reversed)
#         for count, date in enumerate(dates):
#             if date.date == shipment[send_date_field]:  # if date object matches reversed string
#                 shipment[date_object_field] = date
#                 print("DATE MATCH - Shipment for", shipment[customer_field], "can be collected on",
#                       shipment[date_object_field].date, "\n")
#                 manifest[ship_count] = shipment
#                 pprint(manifest[ship_count])
#                 break  # out of the date loop, back to shipment loop
#
#         else:  # no date match
#             print("\nNO COLLECTION ON SEND OUT DATE FOR", shipment[customer_field], "\n")
#             if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
#                 for count, date in enumerate(dates):
#                     print(count + 1, date.date)
#                 choice = int(input("\nChoose a Date\n")) - 1
#                 shipment[date_object_field] = dates[choice]
#                 manifest[ship_count] = shipment
#                 print("shipcouint", ship_count + 1)
#
#                 print("Collection Date Is Now ", shipment[date_object_field].date, "\n")
#                 # continue
#             manifest.remove(shipment)
#             print('Shipment Removed "' + shipment[customer_field] + '" .... Moving On\n')
#         print(shipment[customer_field])
#         # get_date_objects(manifest)
#     return (manifest)
def get_manifest_address_objects(manifest):
    for count, shipment in enumerate(manifest, start=1):
        # set search string - number or firstline
        if shipment[building_num_field] == 0: shipment[building_num_field] = False
        if not shipment[building_num_field]:
            search_string = shipment[address_firstline_field]
        else:
            search_string = shipment[building_num_field]
        # get object
        address_object = client.find_address(shipment[postcode_field], search_string)
        manifest[count - 1][address_object_field] = address_object
    return manifest

#
# def get_shipment_date_object(shipment):
#     print(shipment[customer_field], "Getting Dates")
#
#     dates = client.get_available_collection_dates(sender, courier_id)
#
#     send_date_reversed = shipment[send_date_field].split("/")
#     send_date_reversed.reverse()
#     shipment[send_date_field] = '-'.join(send_date_reversed)
#
#     for count, date in enumerate(dates):
#         if date.date == shipment[send_date_field]:  # if date object matches reversed string
#             shipment[date_object_field] = date
#             print("DATE MATCH - Shipment for", shipment[customer_field], "can be collected on",
#                   shipment[date_object_field].date, "\n")
#             return shipment
#     else:  # no date match
#         print("\nNO COLLECTION AVAILABLE FOR", shipment[customer_field], "\n")
#         if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
#             for count, date in enumerate(dates):
#                 print(count + 1, date.date)
#             choice = int(input("\nChoose a Date, 0 to cancel and move on\n") + 1)
#             if choice == 0:
#                 return 1
#             else:
#                 shipment[date_object_field] = dates[choice]
#                 print("Collection Date Is Now ", shipment[date_object_field].date, "\n")
#                 return shipment
#         else:
#             print("No alternative selected")
#             return 1
