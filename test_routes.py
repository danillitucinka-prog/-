from app import create_app
app = create_app()
rules = list(app.url_map.iter_rules())
print('total rules', len(rules))
print('sample endpoints')
for rule in app.url_map.iter_rules():
    if any(name in rule.endpoint for name in ('index','login','view_post','user_profile')):
        print(rule.endpoint, rule.rule)
