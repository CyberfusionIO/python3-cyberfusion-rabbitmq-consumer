PREFIX=$(CURDIR)/debian/

install: python3-cyberfusion-rabbitmq-consumer

python3-cyberfusion-rabbitmq-consumer: PKGNAME	:= python3-cyberfusion-rabbitmq-consumer
python3-cyberfusion-rabbitmq-consumer: PKGPREFIX	:= $(PREFIX)/$(PKGNAME)
python3-cyberfusion-rabbitmq-consumer: SDIR		:= python

python3-cyberfusion-rabbitmq-consumer:
	rm -rf $(CURDIR)/build
	python3 setup.py install --force --root=$(PKGPREFIX) --no-compile -O0 --install-layout=deb
# Directory for configuration files (to specify with --config-file-path=<config-file-path>)
	mkdir -p $(PKGPREFIX)/etc/cyberfusion/rabbitmq/

clean:
	rm -rf $(PREFIX)/python3-cyberfusion-rabbitmq-consumer/
	rm -rf $(PREFIX)/*debhelper*
	rm -rf $(PREFIX)/*substvars
	rm -rf $(PREFIX)/files
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/src/*.egg-info
