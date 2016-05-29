try:
  import xml.etree.cElementTree as ET
except ImportError:
  import xml.etree.ElementTree as ET
from datetime import datetime
import os
import glob
import fileinput

# List of specific product SKUs to set to hold
skusToHold = ["04HS90", "19PS01"]
# List of starts-with substrings of specific product SKUs to set to hold
startsWithToHold = ["01HS", "01RI97", "02CW", "02DD", "02SS", "04AM", "04RIG1", "04SF", "05HS", "06HS", "19HSIFC", "40"]
# List of shipping methods to hold if shipped to POBOX
poboxShippingsToHold = ["1GD", "FES", "FE2", "UG"]
# List of shipping methods to check to cover drop-shipped products
shippingsToCheck = ["FES", "FE2"]
# List of subskus that do not need to go on hold
subskusExceptions = ["11HSLD", "03HS", "04HS"]

# Check shipping methods and adds custom information to specific ones
def checkShipping(root):
  log = ''
  shipvia = root.find('shipvia').text
  # Add custom comment if order is being shipped via FedEx Standard Overnight or FedEx 2 Day Air for possible drop-shipped products
  if shipvia in shippingsToCheck:
    # Shipped via FedEx Standard Overnight
    if shipvia == 'FES':
      if (root.find('custom01').text is not None):
        root.find('custom01').text += "\n\n****Please ship STANDARD OVERNIGHT****"
      else:
        root.find('custom01').text = "****Please ship STANDARD OVERNIGHT****"
    # shipped via FedEx 2 Day Air
    if shipvia == 'FE2':
      if (root.find('custom01').text is not None):
        root.find('custom01').text += "\n\n****Please ship 2-DAY AIR****"
      else:
        root.find('custom01').text = "****Please ship 2-DAY AIR****"
    log += 'Added custom information for shipping method: ' + shipvia + '\n'
  return log

# Remove product exceptions from product list so we don't check over them
def removeExceptions(products):
  for sku in products:
    for subsku in subskusExceptions:
      if subsku in sku:
        products.remove(sku)
  return products
  
# Create a subelement for suborder to add virtual rescue product
def createRescueProduct(root):
	log=""
	# If the last suborder is full, make a new one
	lastSubOrder = len(root.findall('import_ca')) - 1
	if (root[lastSubOrder].find('product05').text is not None):
		rescueSubelement = ET.fromstring("""<import_ca>\n    <altnum/>\n    <lastname/>
    <firstname/>\n    <company/>\n    <address1/>\n    <address2/>\n    <city/>\n    <state/>\n    <zipcode/>
    <cforeign/>\n    <phone/>\n    <comment/>\n    <ctype1/>\n    <ctype2/>\n    <ctype3/>\n    <taxexempt/>
    <prospect/>\n    <cardtype/>\n    <cardnum/>\n    <expires/>\n    <source_key/>\n    <ccatalog/>
    <sales_id/>\n    <oper_id/>\n    <shipvia/>\n    <fulfilled/>\n    <paid/>\n    <continued>Y</continued>
    <useprices>Y</useprices>\n    <multiship>F</multiship>\n    <order_date/>\n    <odr_num>0</odr_num>
    <product01>98PP20</product01>\n    <quantity01>1.0000</quantity01>
    <product02/>\n    <quantity02/>\n    <product03/>\n    <quantity03/>\n    <product04/>\n    <quantity04/>
    <product05/>\n    <quantity05/>\n    <price01>0.0000</price01>\n    <discount01>0.0000</discount01>
    <price02/>\n    <discount02/>\n    <price03/>\n    <discount03/>\n    <price04/>
    <discount04/>\n    <price05/>\n    <discount05/>\n    <slastname/>\n    <sfirstname/>\n    <scompany/>
    <saddress1/>\n    <saddress2/>\n    <scity/>\n    <sstate/>\n    <szipcode/>\n    <holddate/>\n    <paymethod/>
    <greeting1/>\n    <greeting2/>\n    <promocred/>\n    <shipping/>\n    <email/>\n    <country/>\n    <scountry/>
    <phone2/>\n    <sphone/>\n    <sphone2/>\n    <semail/>\n    <ordertype/>\n    <inpart/>\n    <title/>\n    <salu/>
    <hono/>\n    <ext/>\n    <ext2/>\n    <stitle/>\n    <ssalu/>\n    <shono/>\n    <sext/>\n    <sext2/>
    <ship_when/>\n    <greeting3/>\n    <greeting4/>\n    <greeting5/>\n    <greeting6/>\n    <password/>\n    <custom01/>
    <custom02/>\n    <custom03/>\n    <custom04/>\n    <custom05/>\n  </import_ca>""")
		rescueSubelement.find('slastname').text = root[0].find('slastname').text
		rescueSubelement.find('sfirstname').text = root[0].find('sfirstname').text
		rescueSubelement.find('saddress1').text = root[0].find('saddress1').text
		rescueSubelement.find('saddress2').text = root[0].find('saddress2').text
		rescueSubelement.find('scity').text = root[0].find('scity').text
		rescueSubelement.find('sstate').text = root[0].find('sstate').text
		rescueSubelement.find('szipcode').text = root[0].find('szipcode').text
		rescueSubelement.find('scountry').text = root[0].find('scountry').text
		rescueSubelement.find('sphone').text = root[0].find('sphone').text
		rescueSubelement.find('semail').text = root[0].find('semail').text
		rescueSubelement.find('sphone').text = root[0].find('sphone').text
		root.append(rescueSubelement)
		log += "_rescue found. Virtual rescue product created\n"
	else:
		sub = root[lastSubOrder]
        # Loop through products 1 to 5 and set first None product to rescue virtual product
		for i in range(1, 6):
			if (sub.find('product0' + str(i)).text is None):
				sub.find('product0' + str(i)).text = '98PP20'
				sub.find('quantity0' + str(i)).text = '1.0000'
				sub.find('price0' + str(i)).text = '0.0000'
				sub.find('discount0' + str(i)).text = '0.0000'
				break
		log += "_rescue found. Virtual rescue product created\n"
	return log

# Removes substring from end of string if exists in root
def removeEnd(root, end):
	found = False
	for subroot in root:
		for i in range(1, 6):
			if (subroot.find('product0' + str(i)).text is None):
				break
			elif (subroot.find('product0' + str(i)).text[-len(end):] == end):
				found = True
				subroot.find('product0' + str(i)).text = subroot.find('product0' + str(i)).text[:-len(end)]
	return found

# Return a list of products in the order
def createProductList(root):
  products = []

  for subroot in root:
    for i in range(1, 6):
      if (subroot.find('product0' + str(i)).text is None):
        break
      else:
        products.append(subroot.find('product0' + str(i)).text)
  return products
  
# Check the product list and returns a log if hold condition is met
def checkProducts(products):
  log = ''
  
  # If a product has a Hale Petdoor with same interior and exterior color 
  intColor = [product for product in products if "19HSifc" in product]
  extColor = [product for product in products if "03HS" in product or "04HS" in product]
  load = [product for product in products if "11hsld" in product]
  list = [int for int in intColor for ext in extColor if int[-1] == ext[-2]]
  if list:
	log += 'Found Hale Petdoor with the same interior and exterior color: ' + ', '.join(intColor) + '. Contact customer about matching colors.\n'
  # Remove from products to check
  products = [product for product in products if product not in intColor + extColor + load]
  
  # If a product contains SKU '01PPC' and ('X', 'Y', or 'Z')
  list = [product for product in products if "01PPC" in product and any(custom in product for custom in ('X','Y','Z'))]
  if list:
    products = [product for product in products if product not in list]
    log += 'Custom Thermo Panel(s). Make sure correct height selected: ' + ', '.join(list) + '\n'
  
  list = [product for product in products if product in skusToHold]
  # If any of the products' skus is in skus list
  if list:
    products = [product for product in products if product not in list]
    log += 'Found Product SKUs: ' + ', '.join(list) + '\n'

  list = [product for product in products if product.startswith(tuple(startsWithToHold))]
  # If any of the products starts with any of the substrings in starts-with list
  if list:
    products = [product for product in products if product not in list]
    log += 'Found Starts-With Product Partial SKUs: ' + ', '.join(list) + '\n'
  
  # If two or more products are ordered to check
  if len(products) >= 2:
    log += 'Found two or more products being ordered to check: ' + ', '.join(products) + '\n'

  return log
  
# checkHold returns a log if any hold condition is met
def checkHold(root):
  log = ''
  shipChange = False
  
  # Check all the products for hold
  log += checkProducts(createProductList(root))
  
  # If a rescue product was found, add the virtual rescue product and remove "_rescue" from rescue product skus
  if removeEnd(root, "_rescue"):
    log += createRescueProduct(root)
  
  # Only need to check the first child for name and shipping information
  subroot = root[0]
  
  # If Dick Dixon orders
  if subroot.find('lastname').text == 'Dixon' and subroot.find('firstname').text == 'Dick':
    log += 'Order placed by ' + subroot.find('firstname').text + ' ' + subroot.find('lastname').text + '. Add Signature Required\n'
  
  first = subroot.find('firstname').text
  last = subroot.find('lastname').text
  card = subroot.find('cardholder').text
  # If credit card name exists and any account, cardholder, and shipping names do not match
  if card and (first + " " + last != card or first != subroot.find('sfirstname').text or last != subroot.find('slastname').text):
    log += 'Possible fraud order. First and last names do not all match up between account, cardholder, and shipping\n'
  
  shipvia = subroot.find('shipvia').text
  
  # If no shipping method
  if shipvia is None:
    log += 'Shipvia: No Shipping Method\n'
  # If order will be picked up/will call in
  elif shipvia == 'WC':
    log += 'Shipvia: Will Call/Pick Up order\n'
  # If order is being shipped via UPS
  elif 'UPS Ground' in shipvia:
    subroot.find('shipvia').text = 'UG'
    shipChange = True
  # If order is being shipped via FedEx Smart Post
  elif shipvia == 'FedEx - Smart Post':
    subroot.find('shipvia').text = 'FSP'
    shipChange = True
  # If order is being shipped internationally
  if subroot.find('scountry').text != 'US':
    log += 'Scountry: International\n'
  # If order is being shipped to a possible P.O. Box via FedEx (1 Day Ground, Standard Overnight, 2 Day Air) or UPS
  if ((subroot.find('saddress1').text is not None and 'p' == subroot.find('saddress1').text[0].lower() or
       subroot.find('saddress2').text is not None and 'p' == subroot.find('saddress2').text[0].lower()) and
       shipvia in poboxShippingsToHold):
    log += 'Saddress1/Saddress2 and Shipvia: Possible P.O. Box ship and ' + shipvia + '\n'
  
  # If promo_code is a set discount (ends with "!")
  if (subroot.find('promo_code').text is not None and subroot.find('promo_code').text[-1:] == '!'):
    log += "promo_code '" + subroot.find('promo_code').text + "' is a set amount (ends with '!')\nCoupon code in MOM\n"
  
  return log, shipChange

# Add years to date d
def add_years(d, years):
    """Return a date that's `years` years after the date (or datetime)
    object `d`. Return the same calendar date (month and day) in the
    destination year, if it exists, otherwise use the following day
    (thus changing February 29 to March 1).
    """
    try:
        return d.replace(year = d.year + years)
    except ValueError:
        return d + (datetime(d.year + years, 1, 1).date() - datetime(d.year, 1, 1).date())

# Set the hold date to current date plus 'holdYears' years
def setHolddate(root, holdYears):
  holddate = add_years(datetime.now().date(), holdYears)
  root.find('holddate').text = str(holddate)
  return 'Hold date set to: ' + str(holddate) + '\n'

# Main function to run script
def main():
  # Path of the working directory to change to for parsing
  fromPath = 'C:\Xtento\Download\data'
  toPath = 'C:\Xtento\Download\parsed'
  # Change the current working directory to the one to parse through
  os.chdir(fromPath)
  
  files = glob.glob('*.xml')
  if files:
    orderlog = ''
    # For each XML file, parse each
    for file in files:
		log = ''
		shipChange = False
		products = []
		print 'Looking in .xml file: ' + file
		root = ET.parse(file).getroot()
		# Check the shipping methods and add custom info if needed
		checkShipping(root[0])
		# If order is on hold, set the hold date
		log, shipChange = checkHold(root)
		if log:
			# Set hold date by X number of years from now
			orderlog += 'Alternate Order #' + file[11:-4] + '\n' + log + setHolddate(root[0], 4) + '\n'
		if log or shipChange:
			# Write tree back to XML file
			ET.ElementTree(root).write(file)
	# Move parsed and unparsed files to parsed folder
    for file in files:
		os.rename(fromPath + '/' + file, toPath + '/' + file)
	# If something went on hold in any of the files
    if orderlog:
	    # Create a file to write the order log in
		f = open('C:\Users\Administrator\Desktop\logsXtento\orders_' + datetime.now().strftime("%y-%m-%d_%H_%M") + '.txt', 'w')
		f.write(orderlog)

main()
