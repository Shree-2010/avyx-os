# duktape instead of mozjs: avoids building Firefox's JS engine (hours) just for polkit rules.
PACKAGECONFIG:remove = "mozjs"
PACKAGECONFIG:append = " duktape"
