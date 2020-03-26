# -*- coding: utf-8 -*-

""" ESC/POS Commands (Constants) """

# Transaction commands
TXN_OPN_RECPT  = '\x0A\x01'  # Transaction Open Receipt
TXN_ADD_ITEM   = '\x0A\x02'  # Transaction Add Item
TXN_SUB_TOT    = '\x0A\x03'  # Transaction SUBTOTAL
TXN_DISCOUNT   = '\x0A\x04'  # Transaction DISCOUNT
TXN_TIP        = '\x0A\x10'  # Transaction TIP/Donation
TXN_PAYMENT    = '\x0A\x05'  # Transaction PAYMENT
TXN_CLOSE      = '\x0A\x06'  # Transaction CLOSE
TXN_CANCEL	   = '\x0A\x07'  # Cancel Transaction/ Receipt
TXN_SER_CHRG   = '\x0A\x14'  # Service Charge


#Comment Line Command
CMNT_LINE 	   = '\x0A\x12'

#Report Command
Z_CLOSUER 	   	   	= '\x08\x01'  # Z_CLOSUER Report
Z_CLOSUER_DT_RNG   	= '\x09\x01'  # Z_CLOSUER Report by Date Range
Z_CLOSUER_Z_RNG   	= '\x09\x02'  # Z_CLOSUER Report by Z Range
Z_CLOSUER_GET_DATA	= '\x09\x20'  # Z_CLOSUER Report Get Next Data
Z_CLOSUER_FINISH	= '\x09\x21'  # Z_CLOSUER Report Printing Done
Z_CLOSUER_CANCEL	= '\x09\x22'  # Z_CLOSUER Report Printing Cancel
INFO_DT_RNG   		= '\x09\x30'  # INFORMATION Report by Date Range
INFO_Z_RNG    		= '\x09\x31'  # INFROMATION Report by Z Range
X_REPORT  	   		= '\x08\x05'  # X_REPORT


#Date and Time Setting
SET_DATE_TIME  = '\x05\x01'  #Set Date and Time

# Non-Fiscal Document Commands
NFD_OPN_RECPT  = '\x0E\x01'  # NFD Open Receipt
NFD_CLOSE  	   = '\x0E\x06'  # NFD Close Receipt
NFD_PRINT  	   = '\x0E\x02'  # NFD Print single line
