import pymssql, ldap, ConfigParser, sys

config = ConfigParser.ConfigParser()

try:
   config.read(sys.argv[1])
except:
   print "need config .ini file as command line param"
   sys.exit(1)

update_database = False
update_database = not config.get("qcdatabase","dryrun")

print "update_database is ",update_database

oldbase = config.get("oldldap","base")
newbase = config.get("newldap","base")

oldldap = ldap.initialize(config.get("oldldap","url"))
oldldap.protocol_version = ldap.VERSION3
oldldap.set_option(ldap.OPT_REFERRALS, 0)
oldbind = oldldap.simple_bind_s(config.get("oldldap","user"),config.get("oldldap","password"))

newldap = ldap.initialize(config.get("newldap","url"))
newldap.protocol_version = ldap.VERSION3
newldap.set_option(ldap.OPT_REFERRALS, 0)
newbind = newldap.simple_bind_s(config.get("newldap","user"),config.get("newldap","password"))

conn = pymssql.connect(user=config.get("qcdatabase","user"),
                       password=config.get("qcdatabase","password"),
                       host=config.get("qcdatabase","host"),
                       database=config.get("qcdatabase","database") )

cursor = conn.cursor()

query = '''
SELECT [USER_ID]
      ,[USER_NAME]
      ,[ACC_IS_ACTIVE]
      ,[US_DOM_AUTH]
  FROM [dbo].[USERS]
'''
#
# get list of users
#
cursor.execute(query)

accountstoupdate = {}

#
# from list of users, reconcile against the old and new domain. In our case
# users not in both are almost always exited staff or otherwise not used in QC
# so we can pass over them, their LDAP field can be updated manually if really required.
#
for USER_ID,USER_NAME,ACC_IS_ACTIVE,US_DOM_AUTH in cursor.fetchall():
   if US_DOM_AUTH is not None:
       print "looking in ldap for QC username ",USER_NAME
       new_us_dom_auth = US_DOM_AUTH.replace(oldbase,newbase)

       # lets try a user search to see if the new one works....
       attributes = ['displayName']
       try:
          result = oldldap.search_s(US_DOM_AUTH,ldap.SCOPE_BASE,'(objectClass=*)',attrlist=attributes)
 
          results = [entry for dn, entry in result if isinstance(entry, dict)]
          print "could find in old domain:", results
          ldapgoodforold = True
       except Exception, x:
          # print "Exception ",x
          ldapgoodforold = False
          print " couldnt find in old domain",US_DOM_AUTH

       try:
          result = newldap.search_s(new_us_dom_auth,ldap.SCOPE_BASE,'(objectClass=*)',attrlist=attributes)
 
          results = [entry for dn, entry in result if isinstance(entry, dict)]
          print "could find in New Domain:", results
          ldapgoodfornew = True
       except Exception, x:
          # print "Exception ",x
          print " couldnt find in New Domain ",new_us_dom_auth
          ldapgoodfornew = False

       # gather list to ugrade
       if ldapgoodfornew and ldapgoodforold and not new_us_dom_auth == '':
          accountstoupdate[USER_NAME] = new_us_dom_auth
          
oldldap.unbind()
newldap.unbind()

#
# now actually update in the database.
#

for user_name in accountstoupdate.keys():
   updatesql = '''UPDATE [dbo].[USERS]
                  SET [US_DOM_AUTH] = '%s'
                  WHERE [USER_NAME] = '%s' ''' % (accountstoupdate[user_name],user_name)

   if update_database:
      cursor.execute(updatesql)  
   else:
      print "dummy run: WOULD RUN SQL ",updatesql

conn.commit()
conn.close()
