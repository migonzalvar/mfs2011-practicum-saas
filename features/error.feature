Feature: Error
	As an API client
	In order to have meaningful error codes
	I want to understand

	Scenario: Trying to fetch an inexistent resource
		When I get a bogus URL
		Then I fail with 404
