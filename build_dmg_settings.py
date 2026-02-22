import os.path

# Define target elements required by dmgbuild
application = 'dist/MG400_AI_Generator.app'
appname = os.path.basename(application)

# Define disk properties
format = 'UDZO'
files = [ application ]

# Include intuitive drag & drop symlink automatically inside mac dmg windows
symlinks = { 'Applications': '/Applications' }

# Icons or styling can be defined here if provided
badge_icon = None
icon = None
window_rect = ((100, 100), (600, 400))
