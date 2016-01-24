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
       shipvia in poboxShippingsToHold):if ('p' == root.find('saddress1').text[0].lower or 'p' == root.find('saddress2').text[0].lower) and shipvia in poboxShippingsToHold:
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
		print 'Looking in .xml file: ' + file
		root = ET.parse(file).getroot()
		# Start at the more relevant root: import_ca
		subroot = root[0]
		# Check the shipping methods and add custom info if needed
		checkShipping(subroot)
		# Check and add holddate if conditions are met
		olog, onHold = checkHold(subroot)
		log += olog
		if (onHold):
			# Set hold date by X number of years from now
			log += setHolddate(subroot, 4)
			# Write tree back to XML file
			ET.ElementTree(root).write(file)
			orderlog += 'Alternate Order #' + file[11:-4] + '\n' + log + '\n'
    if orderlog != '':
	    # open file to write order log in
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
