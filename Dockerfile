FROM python:3.7.2-alpine

RUN apk update \
        && apk --no-cache add \
            linux-headers \
            gpgme-dev \
            libxml2-dev \
            openssl-dev\
            libc-dev \
            libffi-dev \
            gcc 

COPY . /chat2desk/
WORKDIR /chat2desk

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /chat2desk/requirements.txt

EXPOSE 8009
CMD  python -u chat2desk.py 8009
