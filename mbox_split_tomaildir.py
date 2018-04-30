#!/usr/bin/env python

# Adapted from:
# http://wboptimum.com/splitting-gmail-mbox-by-label/

import sys
import getopt
import mailbox
import time

def main(argv):
	in_mbox = "inbox.mbox"
	out_box = "Maildir"
	try:
		opts, args = getopt.getopt(argv, "i:o:", ["infile=", "outdir="])
	except getopt.GetoptError:
		print("python splitgmail.py -i <infile> -o <outdir>")
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-i", "--infile"):
			in_mbox = arg
		elif opt in ("-o", "--outdir"):
			out_box = arg

	print("Processing file \"" + in_mbox + "\", output \"" + out_box + "\"")
	sys.stdout.flush()

	destMbox = mailbox.Maildir(out_box, create=True)

	# create common subfolders, INBOX is root
	destMbox.add_folder("Sent")
	destMbox.add_folder("Archive")

	sourcembox = mailbox.mbox(in_mbox, create=False)
	print(str(sourcembox.__len__()) + " messages to process")
	sys.stdout.flush()

	mcount = mjunk = mchat = msaved = 0
	for message in sourcembox:
		read = True
		flagged = False
		mcount += 1
		gmail_labels = message["X-Gmail-Labels"]
		# extract delivery date from mbox "From_" field
		ddate = message.get_from()
		ddate = ddate.split(' ', 1)[1]
		depoch = time.mktime(time.strptime(ddate.strip(), "%a %b %d %H:%M:%S +0000 %Y")) - time.timezone
		tbox = "Archive"				# default target box: Archive

		if gmail_labels:
			gmail_labels = gmail_labels.split(',')	# from here we only work on an array to avoid partial matches
			if "Unread" in gmail_labels:
				read = False
			if "Starred" in gmail_labels:
				flagged = True

			if "Spam" in gmail_labels:		# skip all spam
				mjunk += 1
				continue
			elif "Chat" in gmail_labels:		# skip all chat
				mchat += 1
				continue
			elif "Sent" in gmail_labels:		# anything that has Sent goes to Sent box
				tbox = "Sent"
			elif "Inbox" in gmail_labels:		# Inbox treated here because some messages can be Sent,Inbox
				tbox = "Inbox"
			else:
				for label in gmail_labels:
					# ignore meta labels
					if label == "Important" or label == "Unread" or label == "Starred" or label == "Newsletters":
						continue

					# use first match
					tbox = label

					# handle odd labels
					if label == "[Imap]/Archive":
						tbox = "Archive"
					break
				# if nothing matched we'll use default set at message loop start

		# fixup missing status flags in the message
		if read:
			message["Status"] = "RO"
		else:
			message["Status"] = "O"
		if flagged:
			message["X-Status"] = "F"

		mfrom = message["From"] or "Unknown"
		mid = message["Message-Id"] or "<N/A>"
		print("Storing " + mid + " from \"" + mfrom + "\" to folder \"" + tbox + "\"")
		msaved += 1

		# convert message to maildir
		MDmsg = mailbox.MaildirMessage(message)

		# fixup received date
		MDmsg.set_date(depoch)

		if tbox == "Inbox":
			destMbox.add(MDmsg)
		else:
			if tbox not in destMbox.list_folders():
				destMbox.add_folder(tbox)
			tfolder = destMbox.get_folder(tbox)
			tfolder.add(MDmsg)

	print(str(mcount) + " messages processed, " + str(saved) + " messages saved")
	print("ignored: " + str(mjunk) + " spam, " + str(mchat) + " mchat")

if __name__ == "__main__":
    main(sys.argv[1:])
