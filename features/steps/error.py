from behave import then, when


@then("I fail with {code}")
def fail_with_code(context, code):
    status = context.response.status[0:3]
    assert status == code, 'Status is not {code}, is {status}\n{response}'.format(
            code=code, status=status, response=context.response)

@when(u'I get a bogus URL')
def bogus(context):
    context.response = context.client.get('/blablax/', status="*")
