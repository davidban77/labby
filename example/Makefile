project:
	labby project create labby_test

nodes:
	labby node create sw1 -p labby_test -t "Ethernet switch"
	labby node create cloud1 -p labby_test -t Cloud
	labby node create r1 -p labby_test -t "Cisco IOSv 15.7(3)M3"
	labby node create r2 -p labby_test -t "Arista vEOS 4.25.0FX"
	labby node create r3 -p labby_test -t "Cisco CSR1000v 17.3.1a"

links:
	labby link create -p labby_test -na r1 -pa Gi0/0 -nb sw1 -pb Ethernet1
	labby link create -p labby_test -na r1 -pa Gi0/1 -nb r2 -pb Ethernet1
	labby link create -p labby_test -na r1 -pa Gi0/2 -nb r3 -pb Gi2
	labby link create -p labby_test -na r2 -pa Management1 -nb sw1 -pb Ethernet2
	labby link create -p labby_test -na r3 -pa Gi1 -nb sw1 -pb Ethernet3
	labby link create -p labby_test -na r3 -pa Gi3 -nb r2 -pb Ethernet2
	labby link create -p labby_test -na cloud1 -pa eth0 -nb sw1 -pb Ethernet0

start-nodes:
	labby node start r2 -p labby_test
	labby node start r1 -p labby_test
	labby node start r3 -p labby_test

bootstrap-r1:
	labby provision bootstrap r1 -p labby_test -c configs/r1_boot.txt -t cisco_iosxe

bootstrap-r2:
	labby provision bootstrap r2 -p labby_test -c configs/r2_boot.txt -t arista_eos

bootstrap-r3:
	labby provision bootstrap r3 -p labby_test -c configs/r3_boot.txt -t cisco_iosxe

teardown:
	labby node stop r1 -p labby_test
	labby node stop r2 -p labby_test
	labby node stop r3 -p labby_test
	labby project delete labby_test

lab: project nodes links start-nodes bootstrap-r2 bootstrap-r1 bootstrap-r3

