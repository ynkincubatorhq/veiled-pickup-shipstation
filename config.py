"""Configuration for the Shopify -> ShipStation pickup order mapper.

Edit STORE_ADDRESS with the real Veiled Clifton store details before running
against live data. Everything else is unlikely to need changes.
"""

# Shopify order tags that mark an order as a pickup that ShipStation is NOT
# importing automatically. Mirrors the Shopify Flow shown in the screenshot.
PICKUP_TAGS = {
    "pickupmolablvd",
    "pickupcliftononly",
    "cliftonpickupsplit",
}

# Veiled flagship store, Clifton NJ.
STORE_ADDRESS = {
    "name": "Veiled Clifton",
    "company": "Veiled",
    "address_line_1": "1132 US Highway 46",
    "address_line_2": "",
    "address_line_3": "",
    "city": "Clifton",
    "state": "NJ",
    "postal_code": "07013",
    "country_code": "US",
    "phone": "+1 973-636-4999",
}

# Per the manager: leave carrier service empty, put the store name in the
# Shipping Service column so ShipStation knows which pickup location to route to.
SHIPPING_SERVICE = "Veiled Clifton"

ORDER_SOURCE = "Shopify"

# ShipStation v3 sample import column order. Keep this list stable so the
# output CSV always matches what ShipStation expects.
SHIPSTATION_COLUMNS = [
    "Order #",
    "Order Date",
    "Date Paid",
    "Order Total",
    "Amount Paid",
    "Tax",
    "Shipping Paid",
    "Shipping Service",
    "Height(in)",
    "Length(in)",
    "Width(in)",
    "Weight(oz)",
    "Custom Field 1",
    "Custom Field 2",
    "Custom Field 3",
    "Order Source",
    "Notes to the Buyer",
    "Notes from the Buyer",
    "Internal Notes",
    "Gift Message",
    "Gift Flag",
    "Buyer Full Name",
    "Buyer First Name",
    "Buyer Last Name",
    "Buyer Email",
    "Buyer Phone",
    "Buyer Username",
    "Recipient Full Name",
    "Recipient First Name",
    "Recipient Last Name",
    "Recipient Phone",
    "Recipient Company",
    "Address Line 1",
    "Address Line 2",
    "Address Line 3",
    "City",
    "State",
    "Postal Code",
    "Country Code",
    "Item SKU",
    "Item Name / Title",
    "Item Quantity",
    "Item Unit Price",
    "Item Weight (oz)",
    "Item Options",
    "Item Warehouse Location",
    "Item Marketplace ID",
]
