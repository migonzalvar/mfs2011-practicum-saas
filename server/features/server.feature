Feature: Basic agenda manipulation
	As an API client
	In order to interact with the agenda
	I want to perform CRUD operations

	Scenario: Get agenda metadata
		When I get agenda
		Then I see name is Testing

	Scenario: Create a work shift
		When I create a shift on tomorrow from 08:00 to 14:00
		Then I succeed with 201

	Scenario Outline: Make appointments
		Given I have a shift tomorrow from 08:00 to 14:00
		When I make an appointment <date> at <time>
		Then I succeed with 201

	Examples:
			| date     | time  |
			| tomorrow | 08:00 |
			| tomorrow | 08:30 |
			| tomorrow | 09:00 |
			| tomorrow | 09:30 |
			| tomorrow | 10:00 |
			| tomorrow | 10:30 |
			| tomorrow | 11:00 |
			| tomorrow | 11:30 |
			| tomorrow | 12:00 |
			| tomorrow | 12:30 |
			| tomorrow | 13:00 |
			| tomorrow | 13:30 |

	Scenario Outline: Make appointments
		When I make an appointment <date> at <time>
		Then I fail

	Examples:
			| date     | time  |
			| tomorrow | 08:00 |
			| tomorrow | 08:30 |
			| tomorrow | 09:00 |
			| tomorrow | 09:30 |
			| tomorrow | 10:00 |
			| tomorrow | 10:30 |
			| tomorrow | 11:00 |
			| tomorrow | 11:30 |
			| tomorrow | 12:00 |
			| tomorrow | 12:30 |
			| tomorrow | 13:00 |
			| tomorrow | 13:30 |

	Scenario: Create 2 shifts and 2 appointments
		Given I have these shifts:
			| date  | start |   end |
			| today | 09:00 | 14:00 |
			| today | 10:00 | 12:00 |
		When I make an appointment today at 13:00
		Then I succeed with 201
		When I make an appointment today at 13:00
		Then I fail

