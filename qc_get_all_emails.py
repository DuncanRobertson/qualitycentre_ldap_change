import pymssql, ldap, ConfigParser, sys

#
# simple script to grab email addresses from QC11 server, printed comman seperated
# so easy to paste into email BCC:
#
# quickly hacked down version of the LDAP changer script.
#

config = ConfigParser.ConfigParser()

try:
   config.read(sys.argv[1])
except:
   print "need config .ini file as command line param"
   sys.exit(1)

oldbase = config.get("oldldap","base")
newbase = config.get("newldap","base")

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
      ,[EMAIL]
      ,[ACC_IS_ACTIVE]
      ,[US_DOM_AUTH]
  FROM [dbo].[USERS]
'''

cursor.execute(query)

emails = []

for USER_ID,USER_NAME,EMAIL,ACC_IS_ACTIVE,US_DOM_AUTH in cursor.fetchall():
   if US_DOM_AUTH is not None and ACC_IS_ACTIVE == 'Y':
       new_us_dom_auth = US_DOM_AUTH.replace(oldbase,newbase)

       attributes = ['mail']
       try:
          result = newldap.search_s(new_us_dom_auth,ldap.SCOPE_BASE,'(objectClass=*)',attrlist=attributes)
 
          results = [entry for dn, entry in result if isinstance(entry, dict)]
          emails.append(results[0]['mail'][0])
          goodforleicabio = True
       except Exception, x:
          # print "Exception ",x
          # print " couldnt find in newldapdomain ",new_us_dom_auth
          goodforleicabio = False

newldap.unbind()

conn.commit()
conn.close()

print "number of accounts that could be verified with LDAP found ",len(emails)

for email in emails[0:-1]:
   print "%s," % email,
print "%s" % emails[-1]
   
