# Requirements Document

## Introduction

This document outlines the requirements for building a comprehensive Model Context Protocol (MCP) server that provides programmatic access to Splitwise functionality. The MCP server will enable AI agents to interact with Splitwise accounts, manage expenses, groups, friends, and perform natural language resolution of entities. The server will implement secure OAuth 2.0 authentication and provide a complete set of tools for expense management.

## Glossary

- **MCP Server**: A Model Context Protocol server that exposes tools for AI agents to interact with external services
- **Splitwise API**: The RESTful API provided by Splitwise for programmatic access to expense management features
- **OAuth 2.0**: An authorization framework that enables secure delegated access
- **API Key**: An alternative authentication method using a consumer key and secret
- **Expense**: A financial transaction recorded in Splitwise, including cost, description, and split details
- **Group**: A collection of users who share expenses together
- **Friend**: A Splitwise user connected to the current user for expense sharing
- **Natural Language Resolution**: The ability to match user-provided text (like "John" or "roommates") to specific Splitwise entities (users, groups)
- **Category**: A classification for expenses (e.g., Food, Utilities, Entertainment)
- **Currency**: A monetary unit supported by Splitwise (e.g., USD, EUR, GBP)
- **Split**: The division of an expense among multiple users, defining who paid and who owes

## Requirements

### Requirement 1: Authentication and Authorization

**User Story:** As a user, I want to securely authenticate with my Splitwise account so that the MCP server can access my data on my behalf.

#### Acceptance Criteria

1. WHEN the MCP Server is configured, THE MCP Server SHALL support OAuth 2.0 authentication flow
2. WHEN the MCP Server is configured, THE MCP Server SHALL support API Key authentication as an alternative method
3. WHEN authentication credentials are stored, THE MCP Server SHALL store credentials securely in environment variables or configuration files
4. WHEN an API request fails with 401 Unauthorized, THE MCP Server SHALL return a clear error message indicating authentication failure
5. WHEN OAuth tokens expire, THE MCP Server SHALL provide guidance for token refresh

### Requirement 2: Current User Information

**User Story:** As a user, I want to retrieve my current user profile information so that I can verify my identity and access my account details.

#### Acceptance Criteria

1. WHEN the get-current-user tool is invoked, THE MCP Server SHALL retrieve the authenticated user's profile information
2. WHEN user information is retrieved, THE MCP Server SHALL return user ID, name, email, registration status, and picture URLs
3. WHEN the API request fails, THE MCP Server SHALL return appropriate error messages with status codes

### Requirement 3: Expense Management

**User Story:** As a user, I want to create, read, update, and delete expenses so that I can manage my shared financial transactions.

#### Acceptance Criteria

1. WHEN the create-expense tool is invoked with required parameters, THE MCP Server SHALL create a new expense in Splitwise
2. WHEN creating an expense, THE MCP Server SHALL accept cost, description, date, currency, category, group ID, and user split information
3. WHEN the get-expenses tool is invoked, THE MCP Server SHALL retrieve a list of expenses with optional filtering by group, friend, or date range
4. WHEN the get-expense tool is invoked with an expense ID, THE MCP Server SHALL retrieve detailed information for that specific expense
5. WHEN the update-expense tool is invoked with an expense ID, THE MCP Server SHALL update the specified expense with new information
6. WHEN the delete-expense tool is invoked with an expense ID, THE MCP Server SHALL delete the specified expense
7. WHEN expense operations fail, THE MCP Server SHALL return descriptive error messages

### Requirement 4: Group Management

**User Story:** As a user, I want to manage groups so that I can organize shared expenses with different sets of people.

#### Acceptance Criteria

1. WHEN the get-groups tool is invoked, THE MCP Server SHALL retrieve all groups associated with the current user
2. WHEN the get-group tool is invoked with a group ID, THE MCP Server SHALL retrieve detailed information including members, balances, and debts
3. WHEN the create-group tool is invoked, THE MCP Server SHALL create a new group with specified name, type, and initial members
4. WHEN the delete-group tool is invoked with a group ID, THE MCP Server SHALL delete the specified group
5. WHEN the add-user-to-group tool is invoked, THE MCP Server SHALL add a specified user to a group
6. WHEN the remove-user-from-group tool is invoked, THE MCP Server SHALL remove a user from a group if their balance is zero
7. WHEN group operations fail, THE MCP Server SHALL return appropriate error messages

### Requirement 5: Friend Management

**User Story:** As a user, I want to manage my friends list so that I can easily share expenses with people I frequently interact with.

#### Acceptance Criteria

1. WHEN the get-friends tool is invoked, THE MCP Server SHALL retrieve all friends associated with the current user
2. WHEN the get-friend tool is invoked with a user ID, THE MCP Server SHALL retrieve detailed information for that specific friend
3. WHEN the create-friend tool is invoked, THE MCP Server SHALL add a new friend using email and optional name information
4. WHEN the delete-friend tool is invoked with a user ID, THE MCP Server SHALL remove the friendship connection
5. WHEN friend operations fail, THE MCP Server SHALL return descriptive error messages

### Requirement 6: Natural Language Entity Resolution

**User Story:** As an AI agent, I want to resolve natural language references to Splitwise entities so that I can understand user intent without requiring exact IDs.

#### Acceptance Criteria

1. WHEN the resolve-friend tool is invoked with a name or partial name, THE MCP Server SHALL search friends list and return matching users
2. WHEN the resolve-group tool is invoked with a name or partial name, THE MCP Server SHALL search groups list and return matching groups
3. WHEN multiple matches are found, THE MCP Server SHALL return all matches with relevance scoring
4. WHEN no matches are found, THE MCP Server SHALL return an empty result with a descriptive message
5. WHEN resolution is performed, THE MCP Server SHALL use fuzzy matching to handle typos and variations

### Requirement 7: Category and Currency Support

**User Story:** As a user, I want to access supported categories and currencies so that I can create expenses with valid classification and monetary units.

#### Acceptance Criteria

1. WHEN the get-categories tool is invoked, THE MCP Server SHALL retrieve all supported expense categories and subcategories
2. WHEN the get-currencies tool is invoked, THE MCP Server SHALL retrieve all supported currency codes and units
3. WHEN category or currency data is retrieved, THE MCP Server SHALL cache results to minimize API calls
4. WHEN cached data is older than 24 hours, THE MCP Server SHALL refresh the cache

### Requirement 8: Comment Management

**User Story:** As a user, I want to add and manage comments on expenses so that I can provide additional context and communicate with other users.

#### Acceptance Criteria

1. WHEN the create-comment tool is invoked with an expense ID and content, THE MCP Server SHALL create a new comment on the expense
2. WHEN the get-comments tool is invoked with an expense ID, THE MCP Server SHALL retrieve all comments for that expense
3. WHEN the delete-comment tool is invoked with a comment ID, THE MCP Server SHALL delete the specified comment
4. WHEN comment operations fail, THE MCP Server SHALL return appropriate error messages

### Requirement 9: Error Handling and Validation

**User Story:** As a developer, I want comprehensive error handling so that I can understand and resolve issues when they occur.

#### Acceptance Criteria

1. WHEN any API request fails, THE MCP Server SHALL return structured error information including status code and message
2. WHEN required parameters are missing, THE MCP Server SHALL validate inputs and return clear validation errors
3. WHEN rate limits are exceeded, THE MCP Server SHALL return a rate limit error with retry guidance
4. WHEN network errors occur, THE MCP Server SHALL return connection error messages
5. WHEN invalid data formats are provided, THE MCP Server SHALL validate and return format error messages

### Requirement 10: Documentation and Setup

**User Story:** As a user, I want clear documentation so that I can easily set up and use the MCP server.

#### Acceptance Criteria

1. WHEN the MCP Server is distributed, THE MCP Server SHALL include a comprehensive README with setup instructions
2. WHEN documentation is provided, THE MCP Server SHALL include examples for all major operations
3. WHEN authentication is configured, THE MCP Server SHALL provide step-by-step OAuth setup instructions
4. WHEN tools are documented, THE MCP Server SHALL include parameter descriptions and expected responses
5. WHEN troubleshooting is needed, THE MCP Server SHALL include common error scenarios and solutions
