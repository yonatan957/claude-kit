# claude-kit

Claude Kit is a CLI tool that abstracts different sources of skills, MCP servers and plugins and allows textual search 
and installation of said plugins, etc. 

## Possible commands

### ck init
initializes Claude Kit by installing Claude Code, configures it using data pulled over network.

### ck status
checks the versions of all Claude Kit's dependencies, being Claude Kit itself, Claude Code, and remotely pulled configuration files listing recommended plugins for download.
writes the current versions compared to the latest ones available on a persistent file.

### ck upgrade 
uses ck status to find which parts of itself could be upgraded to newer versions, and upgrades.
#### possible flags
* --no-ck: excludes Claude Kit from upgrading.
* --no-cc: excludes Claude Code from upgrading.
* --no-catalog: excludes the list of plugin recommendations from upgrading.

### ck install <skill/agent/mcp> <--source "source_name" >  <--upgrade> “package_name”
install a new package (being a skill, agent or mcp server).
in case of installation that require user input, ck ask you to type values one by one - then install.
#### possible flags
* --source "source_name": Specifies which source to install from.
* --upgrade : upgrade the package if installed

### ck uninstall <skill/agent/mcp> “package_name:tag”
uninstall a local package (being a skill, agent or mcp server).
optionally, you may specify an identifying tag additionally to "package_name" (the tag is the 4 first characters of a hash value on the file itself), in any case there is more than one package sharing a name. 

### ck list <skill/agent/mcp>  
show all skills/agents/tools/mcp installed locally, including metadata such as: name, description, hash value ("tag" from earlier).

### ck search <skill/agent/mcp> <--recommend> “query” 
search for packages in all registered sources of skills/agents/mcp, 
show all skills/agents/tools/mcp installed locally, including metadata such as: name, description, source, stars(optional)

## the registries

### main registry 
will be a git repo belongs to us that will sit on the users computer, containd the skills/mcps/tools etc. (not installed yet)
at ck search <type> --recommend it'll be from the main registry.
the name of the regisry will be genie so ck install --source genie "skill-name" -> install from genie

## other registries
for now we don't have more versions, but there be very soon

## Edge cases
### same skill on two sources
anyway he'll start to install from on source after the other so if he'll install at the previous - so be it, (the first will be genie)