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
# List of substrings of specific product SKUs to set to hold
subskusToHold = ["01HS", "01PP", "02CW", "02DD", "02SS", "04AM", "04RIG1", "04SF", "05HS", "06HS", "12BW", "19HSIFC", "fg", "_rescue"]
# List of shipping methods to hold if shipped to POBOX
poboxShippingsToHold = ["1GD", "FES", "FE2"]
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

# checkHold returns True if any hold condition is met
def checkHold(root):
  hold = False
  log = ''
  
  # Return True if Dick Dixon orders
  if root.find('lastname').text == 'Dixon' and root.find('firstname').text == 'Dick':
    log += 'Order placed by ' + root.find('firstname').text + ' ' + root.find('lastname').text + '. Add Signature Required\n'
    hold = True

  # Add products to a list for easy checking
  products = []
  products.append(root.find('product01').text)
  # Return True if two or more products are ordered
  if root.find('product02').text is not None:
    log += 'Found two or more products being ordered\n'
    hold = True
    products.append(root.find('product02').text)
    if root.find('product03').text is not None:
      products.append(root.find('product03').text)
      if root.find('product04').text is not None:
        products.append(root.find('product04').text)
        if root.find('product05').text is not None:
          products.append(root.find('product05').text)

  list = [sku for sku in skusToHold if sku in products]
  # Return True if any of the products' skus is in skus list
  if list:
    #print 'Found an element of sku list in products list'
    log += 'Found Product SKUs: ' + ', '.join(list) + '\n'
    hold = True

  list = [sku for subsku in subskusToHold for sku in products if subsku in sku]
  # Return True if any of the products' substrings is in subskus list
  if list:
    #print 'Found an element of subsku list as a substring of an element in products list'
    log += 'Found Product Partial SKUs: ' + ', '.join(list) + '\n'
    hold = True

  shipvia = root.find('shipvia').text
  
  # Return True if no shipping method
  if shipvia is None:
    log += 'Shipvia: No Shipping Method\n'
    hold = True
  # Return True if order will be picked up/will call in
  if shipvia == 'WC':
    log += 'Shipvia: Will Call/Pick Up order\n'
    hold = True
  # Return True if order is being shipped internationally
  if root.find('scountry').text != 'US':
    log += 'Scountry: International\n'
    hold = True
  # Return True if order is being shipped via UPS
  if shipvia == 'United Parcel Service - UPS Ground' or shipvia == 'UG':
    log += 'Shipvia: Changed ' + shipvia + ' to UG\n'
    root.find('shipvia').text = 'UG'
    hold = True
  # Return True if order is being shipped to a possible P.O. Box via FedEx (1 Day Ground, Standard Overnight, 2 Day Air)
  if ((root.find('saddress1').text is not None and 'p' == root.find('saddress1').text[0].lower() or
       root.find('saddress2').text is not None and 'p' == root.find('saddress2').text[0].lower()) and
       shipvia in poboxShippingsToHold):
    log += 'Saddress1/Saddress2 and Shipvia: Possible P.O. Box ship and ' + shipvia + '\n'
    hold = True
    
  # Returns False if no condition is met
  return (log, hold)

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

# Removes substring from end of string if exists
def removeEnd(root, end):
	for i in range(1, 6):
		if (root.find('product0' + str(i)).text is None):
			break
		elif (root.find('product0' + str(i)).text[-len(end):] == end):
			root.find('product0' + str(i)).text = root.find('product0' + str(i)).text[:-len(end)]

# Main function to run script
def main():
  # Path of the working directory to change to for parsing
  #path = 'C:\Users\sthon\Desktop\dataxml'
  path = 'C:\Xtento\Download\data'
  # Change the currect working directory to the one to parse through
  os.chdir(path)
  #print 'Current working directory changed to: ' + os.getcwd()
  
  files = glob.glob('*.xml')
  if files:
    orderlog = ''
    # For each XML file, parse each
    for file in files:
		log = ''
		count = 1
		onHold = False
		print 'Looking in .xml file: ' + file
		root = ET.parse(file).getroot()
		# For each suborder in the order
		for subroot in root:
			# Check the shipping methods and add custom info if needed
			checkShipping(subroot)
			# Check and add holddate if conditions are met
			olog, onHold = checkHold(subroot)
			if (onHold):
				log += 'Found hold in products ' + str(count) + '-' + str(count + 4) + '\n' + olog
				# Set hold date by X number of years from now
				log += setHolddate(subroot, 4)
			count += 5
		# If a rescue product was found, add the virtual rescue product
		if ('_rescue' in log):
			for subroot in root:
				removeEnd(subroot, "_rescue")
			orderlog += createRescueProduct(root)
		if onHold:
			orderlog += 'Alternate Order #' + file[11:-4] + '\n' + log + '\n'
			# Write tree back to XML file
			ET.ElementTree(root).write(file)
	# If something went on hold
    if orderlog != '':
	    # Open file to write order log in
		f = open('C:\Users\Administrator\Desktop\logsXtento\orders_' + datetime.now().strftime("%y-%m-%d_%H_%M") + '.txt', 'w')
		f.write(orderlog)

  #file = ''
  #for line in fileinput.input():
    #file = file + line
  
  #root = ET.fromstring(file)

  #if (checkHold(root[0])):
  #setHolddate(root[0], 3)
  #print "holddate:" + root[0].find('holddate').text
    
  # print each child and its text value
  #for child in root[0]:
  #	print child, child.tag, child.text
  	
  # Write tree back to XML file
  # ET.ElementTree(root).write(file)
  
  # Prints out XML of root for debugging purposes
  # ET.dump(root)
  
main()
