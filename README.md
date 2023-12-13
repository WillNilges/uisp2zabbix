(not so) Spiritual successor to:
https://github.com/andybaumgar/nycmesh-metrics-logger/

This is a tool that brokers data from the UISP API and pushes it to Zabbix.

Why? Because Ubiquiti's SNMP implementation is totally busted on the AF60-XR and their ticketing system doesn't work so I can't even tell them about it.

`docker run --rm -d --env-file .env -v ./log:/opt/uisp2zabbix/log --name uisp2zabbix willnilges/uisp2zabbix:main`
