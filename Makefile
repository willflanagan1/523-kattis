all:
	echo "Making web directory"
	(cd web; $(MAKE))
	echo "Making mypoll directory"
	(cd mypoll/src; $(MAKE))
