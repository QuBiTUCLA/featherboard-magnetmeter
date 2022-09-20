import usb_cdc
print("usb_cdc.data is enabled: ")
print(usb_cdc.data)
print("enabling usb_cdc.data")
if usb_cdc.data == None:
    print("usb_cdc.data is enabled: ")
    usb_cdc.enable(console=False, data=True)

print(usb_cdc.data)
