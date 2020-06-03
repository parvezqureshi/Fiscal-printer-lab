ERROR_CODE = {
    # 5.2.1 Essential Returns (00):
    "0000": "Successful Result",
    "0001": "Internal Error",
    "0002": "Printer Initialization Error",
    "0003": "Internal process error",

    # 5.2.2 Return on Generic Commands (01):
    "0101": "Invalid command for the current status",
    "0102": "Invalid command for the current document",
    "0103": "Command accepted only in technical mode",
    "0104": "Command accepted only without Service Jumper",
    "0105": "Command accepted only with Service Jumper",
    "0106": "Command accepted only without Jumper of unlocking by Software",
    "0107": "Command accepted only with Jumper of unlocking by Software",
    "0108": "Scan or logos load process in progress",
    "0109": "Too many technical interventions",

    # 5.2.3 Returns on Protocol Fields (02):
    "0201": "The frame does not contain the minimum length accepted",
    "0202": "Invalid Command",
    "0203": "Fields in excess",
    "0204": "Fields in default",
    "0205": "Field not optional",
    "0206": "Invalid alphanumeric field",
    "0207": "Invalid alphabetical field",
    "0208": "Invalid numerical field",
    "0209": "Invalid binary field",
    "020A": "Invalid printable field",
    "020B": "Invalid hexadecimal field",
    "020C": "Invalid date field",
    "020D": "Invalid time field",
    "020E": "Invalid rich text fiscal field",
    "020F": "Invalid Boolean field",
    "0210": "Invalid field length",
    "0211": "Invalid command extension",
    "0212": "Bar code not allowed",
    "0213": "Printing Attributes not allowed",
    "0214": "Invalid Printing Attributes",
    "0215": "Barcode incorrectly defined",

    # 5.2.4 Returns on Hardware Problems (03):
    "0301": "Hardware Error",
    "0302": "Printer Offline",
    "0303": "Printing Error",
    "0304": "Paper problems, not in conditions for the action required",
    "0305": "Little paper available",
    "0306": "Error in loading or ejecting paper",
    "0307": "Printer feature not supported",
    "0308": "Display Error",
    "0309": "Invalid scan Sequence",
    "030A": "Invalid number of crop area",
    "030B": "Scanner not ready",

    # 5.2.5 Initialization Returns (04):
    "0401": "Invalid Serial Number",
    "0402": "Fiscalization data must be configured",

    # 5.2.6 Setup Returns (05):
    "0501": "Date/Time not set",
    "0502": "Error in date change",
    "0503": "Date out of range",
    "0505": "Invalid number of box",
    "0508": "Invalid header/trailer line number",
    "050C": "Too many types of payments defined",
    "050D": "Type of payment previously defined",
    "050E": "Invalid number of payment",
    "050F": "Invalid payment description",
    "0510": "Reserved",
    "0511": "Invalid digital signature keys",
    "0512": "Digital signature keys not configured",
    "0513": "Invalid user logo",
    "0514": "Invalid sequence of user logos definition",
    "0515": "Invalid display settings",
    "0516": "Invalid MICR font",
    "0523": "Time out in key generation",
    "0538": "Too many free lines for a fiscal receipt.",
    "053A": "Invalid cancellation mode of the ticket.",
    "053B": "CRIB cannot be modified in Fiscalized mode.",
    "053E": "Tax rates cannot be changed.",

    # 5.2.7 Return on Memory Transactions (06):
    "0601": "Electronic Journal Memory full",

    # 5.2.8 Return on Printer Control (07):
    "0705": "Cash Drawer not opened",

    # 5.2.9 Return on Fiscal Day (08):
    "0801": "Invalid command out of fiscal day",
    "0802": "Invalid command within fiscal day",
    "0803": "Fiscal memory full. Unable to open the fiscal day",
    "0804": "Z closure required",
    "0805": "Payments not defined",
    "0806": "Too many payments used in the fiscal day",
    "0807": "No data for audited period",
    "0808": "Invalid Audited Range",
    "0809": "There are still more data to download",

    # 5.2.10 Return on Generic Transactions (09):
    "0901": "Overflow",
    "0902": "Underflow",
    "0903": "Too many items involved in the transaction",
    "0904": "Too many tax rates used",
    "0905": "Too many discounts/uplifts on the subtotal involved in the transaction",
    "0906": "Too payments involved in the transaction",
    "0907": "Item not found",
    "0908": "Payment not found",
    "0909": "The total must be greater than zero",
    "090C": "Type of payment not defined",
    "090D": "Too many donations",
    "090E": "Donation Not Found",
    "090F": "VAT Rate not found",

    # 5.2.11 Return on Fiscal Receipt (0A):
    "0A01": "Not allowed after discounts/uplifts on the subtotal",
    "0A02": "Not allowed after initiating the payment stage",
    "0A03": "Invalid item type",
    "0A04": "Line description in blank",
    "0A05": "Resulting quantity less than zero",
    "0A06": "Resulting quantity greater than allowed",
    "0A07": "Total Item Price greater than allowed",
    "0A08": "Not allowed before initiating the payment stage",
    "0A09": "Payment stage not finished",
    "0A0A": "Payment stage finished",
    "0A0B": "Quantity of payment not allowed",
    "0A0C": "Quantity of discount not allowed",
    "0A0D": "Quantity of donation not allowed",
    "0A0E": "Change no greater than zero",
    "0A0F": "Not allowed before an item",
    "0A22": "Invalid quantity",
    "0A25": "Discount/uplift operation not allowed",
    "0A26": "Comment lines were printed",
    "0A2D": "Comment lines limit reached",

    # 5.2.12 Returns on Non-Fiscal Documents (0D):
    "0E01": "Lines limit reached",

    # 5.2.13 Return on Manufacture commands (FF)
    "FF00": "Fiscal Pattern empty",
    "FF01": "Fiscal Pattern not found",
    "FF02": "Invalid Number of Fiscal Pattern",
    "FF03": "Fiscal Pattern in use",
    "FF04": "Fiscal Pattern with error",
    "FF05": "Internal Error in Electronic journal memory",
    "FF06": "Wait Error in Reading/Writing Electronic journal memory",
    "FF07": "Electronic journal memory block with error",

    # 5.2.14 Others (FF):
    "FFFF": "Unknown Error",
}

def convert_to_hex(number):
    return format(int(number), 'x').zfill(4).upper()

def get_error_message(number):
    key = convert_to_hex(number)
    # return ERROR_CODE.get(key, "Error!")
    return ERROR_CODE[key]
