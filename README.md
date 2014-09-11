qualitycentre_ldap_change
=========================

Script for changing the LDAP domain of a QualityCentre install, plus list the user email addresses

Written in Python 2.X with pymssql extension for talking to MS-SQL, testing on Ubuntu 10 against Quality Centre 10 and 11

This is a very rough and ready script that operates on the backend MS-SQL database.

NO GUARANTEES WHATSOEVER! except it has worked for me, so perhaps it will save some typing.

Quality Centre itself needs to be shut down before this script is run.
BUT, you have to have set the new LDAP config in the QC admin console just before you do shut down, so it will work when you start it up.
Backup everything to a recoverable state before going anywhere near this script!

It does have dryrun mode to just display the SQL updates it would do rather than doing them.

An additional script will produce a comma delimited list of email addresses of active users in the new domain, for alerting QC users.

