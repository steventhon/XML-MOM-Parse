try:
  import xml.etree.cElementTree as ET
except ImportError:
  import xml.etree.ElementTree as ET
from datetime import datetime
import os
import glob

# List of specific product SKUs to set to hold
skusToHold = ["19PS01", "04HS90"]
# List of substrings of specific product SKUs to set to hold
subskusToHold = ["01HS", "01PP", "01RI", "06HS", "02SS", "02DD", "19HSIFC", "02CW", "12BW", "fg", "04RIG1", "04SFpdKit", "04AM"]
# List of shipping methods to hold if shipped to POBOX
shippingsToHold = ["1GD", "FES", "FE2"]

# checkHold returns True if any hold condition is met
def checkHold(root):
  hold = False

  # Add products to a list for easy checking
  products = []
  products.append(root.find('product01').text)
  if root.find('product02').text is not None:
    products.append(root.find('product02').text)
    if root.find('product03').text is not None:
      products.append(root.find('product03').text)
      if root.find('product04').text is not None:
        products.append(root.find('product04').text)
        if root.find('product05').text is not None:
          products.append(root.find('product05').text)
  #print products

  list = [sku for sku in skusToHold if sku in products]
  # Return True if any of the products' skus is in skus list
  if list:
    #print 'Found an element of sku list in products list'
    print 'Found Product SKUs: ' + ''.join(list)
    hold = True

  list = [sku for subsku in subskusToHold for sku in products if subsku in sku]
  # Return True if any of the products' substrings is in subskus list
  if list:
    #print 'Found an element of subsku list as a substring of an element in products list'
    print 'Found Product Partial SKUs: ' + ''.join(list)
    hold = True

  shipvia = root.find('shipvia').text
  
  # Return True if no shipping method
  if shipvia is None:
    print 'Shipvia: No Shipping Method'
    hold = True
  # Return True if order will be picked up/will call in
  if shipvia == 'WC':
    print 'Shipvia: Will Call/Pick Up order'
    hold = True
  # Return True if order is being shipped internationally
  if root.find('scountry').text != 'US':
    print 'Scountry: International'
    hold = True
  # Return True if order is being shipped to POBOX via FedEx (1 Day Ground, Standard Overnight, 2 Day Air)
  if 'POBOX' in root.find('saddress1').text  and shipvia in shippingsToHold:
    print 'Saddress1 and Shipvia: POBOX and ' + shipvia
    hold = True

  # Returns False if no condition is met
  return hold

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
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

# Set the hold date to current date plus 'holdYears' years
def setHolddate(root, holdYears):
  holddate = add_years(datetime.now().date(), 3)
  root.find('holddate').text = str(holddate)

# Main function to run script
def main():
  # Path of the working directory to change to for parsing
  path = 'C:\Users\sthon\Desktop\dataxml'
  # Change the currect working directory to the one to parse through
  os.chdir(path)
  #print 'Current working directory changed to: ' + os.getcwd()
  
  files = glob.glob('*.xml')
  # For each XML file, parse each
  for file in files:
    print 'Looking in .xml file: ' + file
    root = ET.parse(file).getroot()
    # Start at the more relevant root: import_ca
    subroot = root[0]
    # Check and add holddate if conditions are met
    if (checkHold(subroot)):
      # Set hold date by X number of years from now
      setHolddate(subroot, 3)
      # Write tree back to XML file
      #ET.ElementTree(root).write(file)

  #file = ''
  #for line in fileinput.input():
    #file = file + line
  
  #root = ET.fromstring(file)

  #if (checkHold(order)):
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
