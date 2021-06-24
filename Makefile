PREFIX=$(CURDIR)/debian/

install: python-cyberfusion-cluster-rabbitmq-consumer

python-cyberfusion-cluster-rabbitmq-consumer: PKGNAME	:= python-cyberfusion-cluster-rabbitmq-consumer
python-cyberfusion-cluster-rabbitmq-consumer: PKGPREFIX	:= $(PREFIX)/$(PKGNAME)
python-cyberfusion-cluster-rabbitmq-consumer: SDIR		:= python

python-cyberfusion-cluster-rabbitmq-consumer:
	rm -rf $(CURDIR)/build
	python3 package-setup.py install --force --root=$(PKGPREFIX) --no-compile -O0 --install-layout=deb
	mkdir -p $(PKGPREFIX)/etc/cyberfusion/rabbitmq/

clean:
	rm -rf $(PREFIX)/python-cyberfusion-cluster-rabbitmq-consumer/
	rm -rf $(PREFIX)/*debhelper*
	rm -rf $(PREFIX)/*substvars
	rm -rf $(PREFIX)/files
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/src/*.egg-info
