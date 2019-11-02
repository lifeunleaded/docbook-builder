FROM alpine
RUN apk add --no-cache curl python openjdk8 py-setuptools git libxml2 libxslt py-lxml zip fontconfig wget tidyhtml findutils tree
COPY fop-1.1 /fop-1.1
COPY fonts /usr/share/fonts
RUN easy_install-2.7 pip
RUN pip install gitpython pyang
