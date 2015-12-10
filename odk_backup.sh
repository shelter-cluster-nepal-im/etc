#!/bin/bash
mysqldump -u scadmin -p'clusteringshelter()' --all-databases > /home/ec2-user/mysql_backup/db.$(date +%m.%d.%y:%H).dump
find /home/ec2-user/mysql_backup/ -cmin -5 | xargs -ILIST aws s3 cp LIST s3://shelter-cluster/odk-backups/$(date +%y)/$(date +%m)/$(date +%d)/
find /home/ec2-user/mysql_backup/ -mtime +3 | xargs -ILIST rm LIST
