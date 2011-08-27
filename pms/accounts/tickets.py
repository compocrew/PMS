#!/usr/bin/env python
from accounts.models import Ticket,TicketType
import sys
from party.models import Party


def main():
	try:
		if len(sys.argv) < 4:
			print "usage: %s partyslug tickettype filename" % sys.argv[0]
			sys.exit(0)

		try:
			party = Party.objects.get(slug=sys.argv[1])
		except Party.DoesNotExist:
			print "Party does not exist"
			sys.exit(-1)
		
		ttype = sys.argv[2]
		filename = sys.argv[3]
	
		try:
			ticketType = TicketType.objects.get(name=ttype)
		except TicketType.DoesNotExist:
			print "Tickettype %s doesn't exist" % ttype
			sys.exit(-1)
		
		print "reading tickets from %s..." % filename
		f = open(filename)
		tickets = []
		for line in f.readlines():
			line = line.strip()
			tickets.append(line)
		
		print "%d tickets loaded" % len(tickets)
		print "adding tickets..."
	
		i = 0
		for ticket in tickets:
			try:
				t = Ticket.objects.get(party=party,code=ticket)
				print "Duplicate ticket '%s' found, skipping" % ticket
			except Ticket.DoesNotExist:
				t = Ticket(ticket_type=ticketType,code=ticket,party=party)
				t.save()
		
			i+=1
			if (i % 100) == 0:
				print "%d added..." % i
	except KeyboardInterrupt:
		print "Break"
		
		
		
if __name__ == '__main__':
	main()