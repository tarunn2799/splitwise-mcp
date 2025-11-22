# Splitwise MCP Server - Tool Reference

This document provides comprehensive documentation for all MCP tools provided by the Splitwise MCP Server.

## Table of Contents

- [User Tools](#user-tools)
- [Expense Tools](#expense-tools)
- [Group Tools](#group-tools)
- [Friend Tools](#friend-tools)
- [Resolution Tools](#resolution-tools)
- [Comment Tools](#comment-tools)
- [Utility Tools](#utility-tools)
- [Error Codes](#error-codes)
- [Common Patterns](#common-patterns)

---

## User Tools

### get-current-user

Get information about the currently authenticated user.

**Parameters:** None

**Returns:**
```json
{
  "user": {
    "id": 12345,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "registration_status": "confirmed",
    "picture": {
      "small": "https://...",
      "medium": "https://...",
      "large": "https://..."
    },
    "default_currency": "USD",
    "locale": "en"
  }
}
```

**Example Usage:**
```
"What's my Splitwise user information?"
```

**Errors:**
- `401`: Authentication failed - check your credentials
- `500`: Splitwise API error

---

### get-user

Get information about a specific user by ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | integer | Yes | The ID of the user to retrieve |

**Returns:**
```json
{
  "user": {
    "id": 67890,
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "picture": {
      "small": "https://...",
      "medium": "https://...",
      "large": "https://..."
    }
  }
}
```

**Example Usage:**
```
"Get information about user 67890"
```

**Errors:**
- `404`: User not found
- `401`: Authentication failed

---

## Expense Tools

### create-expense

Create a new expense in Splitwise.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `cost` | string | Yes | - | Total amount with 2 decimal places (e.g., "25.50") |
| `description` | string | Yes | - | Short description of the expense |
| `group_id` | integer | No | 0 | Group ID (0 for non-group expense) |
| `currency_code` | string | No | "USD" | Three-letter currency code |
| `date` | string | No | current | ISO 8601 datetime string |
| `category_id` | integer | No | null | Category ID from get-categories |
| `users` | array | No | null | List of user split information |
| `split_equally` | boolean | No | true | Whether to split equally among users |

**User Split Format:**
```json
{
  "user_id": 12345,
  "paid_share": "25.00",
  "owed_share": "12.50"
}
```

**Returns:**
```json
{
  "expenses": [{
    "id": 987654,
    "description": "Dinner at restaurant",
    "cost": "50.00",
    "currency_code": "USD",
    "date": "2024-01-15T19:30:00Z",
    "category": {
      "id": 15,
      "name": "Dining out"
    },
    "users": [
      {
        "user_id": 12345,
        "paid_share": "50.00",
        "owed_share": "25.00",
        "net_balance": "25.00"
      },
      {
        "user_id": 67890,
        "paid_share": "0.00",
        "owed_share": "25.00",
        "net_balance": "-25.00"
      }
    ]
  }]
}
```

**Example Usage:**
```
"Create a $45 expense for dinner with Sarah, split evenly"
"I paid $120 for groceries in my Roommates group"
```

**Errors:**
- `400`: Invalid parameters (cost format, currency code, etc.)
- `404`: Group or user not found
- `429`: Rate limit exceeded

---

### get-expenses

Get list of expenses with optional filters.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `group_id` | integer | No | null | Filter by group ID |
| `friend_id` | integer | No | null | Filter by friend user ID |
| `dated_after` | string | No | null | Filter expenses dated after (ISO 8601) |
| `dated_before` | string | No | null | Filter expenses dated before (ISO 8601) |
| `updated_after` | string | No | null | Filter expenses updated after (ISO 8601) |
| `updated_before` | string | No | null | Filter expenses updated before (ISO 8601) |
| `limit` | integer | No | 20 | Max results (1-100) |
| `offset` | integer | No | 0 | Pagination offset |

**Returns:**
```json
{
  "expenses": [
    {
      "id": 123,
      "description": "Groceries",
      "cost": "45.50",
      "currency_code": "USD",
      "date": "2024-01-15T10:00:00Z",
      "users": [...]
    }
  ]
}
```

**Example Usage:**
```
"Show me my expenses from the last 30 days"
"Get expenses in my Roommates group"
"Show expenses with John from last month"
```

**Errors:**
- `400`: Invalid date format or pagination parameters
- `404`: Group or friend not found

---

### get-expense

Get detailed information about a specific expense.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expense_id` | integer | Yes | The ID of the expense to retrieve |

**Returns:**
```json
{
  "expense": {
    "id": 987654,
    "description": "Dinner",
    "cost": "50.00",
    "currency_code": "USD",
    "date": "2024-01-15T19:30:00Z",
    "category": {
      "id": 15,
      "name": "Dining out"
    },
    "users": [...],
    "comments": [...]
  }
}
```

**Example Usage:**
```
"Show me details for expense 987654"
```

**Errors:**
- `404`: Expense not found

---

### update-expense

Update an existing expense.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expense_id` | integer | Yes | The ID of the expense to update |
| `cost` | string | No | New total amount |
| `description` | string | No | New description |
| `date` | string | No | New date (ISO 8601) |
| `category_id` | integer | No | New category ID |
| `users` | array | No | Updated user split information |

**Note:** At least one field must be provided to update.

**Returns:**
```json
{
  "expenses": [{
    "id": 987654,
    "description": "Updated description",
    ...
  }]
}
```

**Example Usage:**
```
"Update expense 987654 to $60"
"Change the description of expense 987654 to 'Team lunch'"
```

**Errors:**
- `400`: No fields provided or invalid parameters
- `404`: Expense not found

---

### delete-expense

Delete an expense permanently.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expense_id` | integer | Yes | The ID of the expense to delete |

**Returns:**
```json
{
  "success": true
}
```

**Example Usage:**
```
"Delete expense 987654"
```

**Errors:**
- `404`: Expense not found
- `403`: Insufficient permissions

---

## Group Tools

### get-groups

Get all groups for the current user.

**Parameters:** None

**Returns:**
```json
{
  "groups": [
    {
      "id": 123,
      "name": "Roommates",
      "group_type": "home",
      "simplify_by_default": true,
      "members": [
        {
          "id": 12345,
          "first_name": "John",
          "last_name": "Doe",
          "balance": [
            {
              "currency_code": "USD",
              "amount": "25.50"
            }
          ]
        }
      ]
    }
  ]
}
```

**Example Usage:**
```
"Show me all my Splitwise groups"
```

---

### get-group

Get detailed information about a specific group.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `group_id` | integer | Yes | The ID of the group to retrieve |

**Returns:**
```json
{
  "group": {
    "id": 123,
    "name": "Roommates",
    "members": [...],
    "original_debts": [...],
    "simplified_debts": [
      {
        "from": 12345,
        "to": 67890,
        "amount": "25.50",
        "currency_code": "USD"
      }
    ]
  }
}
```

**Example Usage:**
```
"Show me details for my Roommates group"
```

**Errors:**
- `404`: Group not found

---

### create-group

Create a new group.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | Group name |
| `group_type` | string | No | "other" | Type: "home", "trip", "couple", or "other" |
| `simplify_by_default` | boolean | No | true | Enable debt simplification |
| `users` | array | No | null | Initial members with user_id, first_name, last_name, email |

**Returns:**
```json
{
  "group": {
    "id": 456,
    "name": "Vacation 2024",
    "group_type": "trip",
    "members": [...]
  }
}
```

**Example Usage:**
```
"Create a group called 'Vacation 2024' for a trip"
"Create a home group called 'Apartment 5B' with John and Sarah"
```

**Errors:**
- `400`: Invalid group_type or parameters
- `404`: User not found (when adding initial members)

---

### delete-group

Delete a group permanently.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `group_id` | integer | Yes | The ID of the group to delete |

**Returns:**
```json
{
  "success": true
}
```

**Example Usage:**
```
"Delete my Roommates group"
```

**Errors:**
- `404`: Group not found
- `400`: Group has unsettled expenses

---

### add-user-to-group

Add a user to a group.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `group_id` | integer | Yes | The ID of the group |
| `user_id` | integer | No* | ID of existing Splitwise user |
| `email` | string | No* | Email address of user to add |
| `first_name` | string | No | First name (used with email) |
| `last_name` | string | No | Last name (used with email) |

**Note:** Either `user_id` or `email` must be provided.

**Returns:**
```json
{
  "success": true,
  "group": {...}
}
```

**Example Usage:**
```
"Add Mike to my Roommates group"
"Add user 67890 to group 123"
```

**Errors:**
- `400`: Neither user_id nor email provided
- `404`: Group or user not found

---

### remove-user-from-group

Remove a user from a group.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `group_id` | integer | Yes | The ID of the group |
| `user_id` | integer | Yes | The ID of the user to remove |

**Returns:**
```json
{
  "success": true
}
```

**Example Usage:**
```
"Remove user 67890 from group 123"
```

**Errors:**
- `400`: User has non-zero balance in group
- `404`: Group or user not found

---

## Friend Tools

### get-friends

Get all friends for the current user.

**Parameters:** None

**Returns:**
```json
{
  "friends": [
    {
      "id": 67890,
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@example.com",
      "balance": [
        {
          "currency_code": "USD",
          "amount": "15.50"
        }
      ],
      "groups": [
        {
          "group_id": 123,
          "balance": [...]
        }
      ]
    }
  ]
}
```

**Example Usage:**
```
"Show me all my Splitwise friends"
```

---

### get-friend

Get detailed information about a specific friend.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | integer | Yes | The ID of the friend to retrieve |

**Returns:**
```json
{
  "friend": {
    "id": 67890,
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "balance": [...],
    "groups": [...]
  }
}
```

**Example Usage:**
```
"Show me details for my friend Jane"
```

**Errors:**
- `404`: Friend not found

---

## Resolution Tools

### resolve-friend

Resolve a natural language friend reference to user ID(s) using fuzzy matching.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Friend name or partial name |
| `threshold` | integer | No | 70 | Minimum match score (0-100) |

**Returns:**
```json
[
  {
    "id": 67890,
    "name": "Jane Smith",
    "match_score": 95.5,
    "additional_info": {
      "email": "jane@example.com",
      "balance": [...]
    }
  }
]
```

**Example Usage:**
```
"Find my friend named Jon" (matches "John Smith")
"Resolve friend 'sara'" (matches "Sarah Johnson")
```

**Matching Behavior:**
- Case-insensitive
- Handles typos and variations
- Matches partial names
- Returns all matches above threshold
- Sorted by match score (highest first)

---

### resolve-group

Resolve a natural language group reference to group ID(s) using fuzzy matching.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Group name or partial name |
| `threshold` | integer | No | 70 | Minimum match score (0-100) |

**Returns:**
```json
[
  {
    "id": 123,
    "name": "Roommates",
    "match_score": 88.0,
    "additional_info": {
      "group_type": "home",
      "members": [...]
    }
  }
]
```

**Example Usage:**
```
"Find group 'roomates'" (matches "Roommates")
"Resolve group 'paris trip'" (matches "Paris Trip 2024")
```

---

### resolve-category

Resolve a natural language category reference to category ID(s) using fuzzy matching.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Category name |
| `threshold` | integer | No | 70 | Minimum match score (0-100) |

**Returns:**
```json
[
  {
    "id": 15,
    "name": "Food and drink",
    "match_score": 92.0,
    "additional_info": {
      "subcategories": [...]
    }
  }
]
```

**Example Usage:**
```
"Find category 'food'" (matches "Food and drink")
"Resolve category 'utilites'" (matches "Utilities")
```

---

## Comment Tools

### create-comment

Create a comment on an expense.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expense_id` | integer | Yes | The ID of the expense |
| `content` | string | Yes | The comment text |

**Returns:**
```json
{
  "comment": {
    "id": 789,
    "content": "This was for the team lunch",
    "user": {
      "id": 12345,
      "first_name": "John",
      "last_name": "Doe"
    },
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

**Example Usage:**
```
"Add a comment to expense 987654: 'Paid with company card'"
```

**Errors:**
- `404`: Expense not found

---

### get-comments

Get all comments for an expense.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expense_id` | integer | Yes | The ID of the expense |

**Returns:**
```json
{
  "comments": [
    {
      "id": 789,
      "content": "This was for the team lunch",
      "user": {...},
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

**Example Usage:**
```
"Show me comments on expense 987654"
```

---

### delete-comment

Delete a comment permanently.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `comment_id` | integer | Yes | The ID of the comment to delete |

**Returns:**
```json
{
  "success": true
}
```

**Example Usage:**
```
"Delete comment 789"
```

**Errors:**
- `404`: Comment not found
- `403`: Can only delete your own comments

---

## Utility Tools

### get-categories

Get all supported expense categories and subcategories.

**Parameters:** None

**Returns:**
```json
{
  "categories": [
    {
      "id": 15,
      "name": "Food and drink",
      "subcategories": [
        {
          "id": 16,
          "name": "Dining out"
        },
        {
          "id": 17,
          "name": "Groceries"
        }
      ]
    },
    {
      "id": 18,
      "name": "Utilities",
      "subcategories": [...]
    }
  ]
}
```

**Example Usage:**
```
"Show me all expense categories"
```

**Note:** This data is cached for 24 hours to minimize API calls.

---

### get-currencies

Get all supported currency codes.

**Parameters:** None

**Returns:**
```json
{
  "currencies": [
    {
      "currency_code": "USD",
      "unit": "$"
    },
    {
      "currency_code": "EUR",
      "unit": "€"
    },
    {
      "currency_code": "GBP",
      "unit": "£"
    }
  ]
}
```

**Example Usage:**
```
"What currencies does Splitwise support?"
```

**Note:** This data is cached for 24 hours to minimize API calls.

---

## Error Codes

All tools may return the following error types:

### Authentication Errors (401)
```json
{
  "error_type": "authentication",
  "message": "Authentication failed. Check your credentials.",
  "status_code": 401
}
```

**Solutions:**
- Verify OAuth access token is correct
- Check that token hasn't expired
- Regenerate token using OAuth setup helper

### Authorization Errors (403)
```json
{
  "error_type": "authorization",
  "message": "Access forbidden. Insufficient permissions.",
  "status_code": 403
}
```

**Solutions:**
- Verify you have permission to access the resource
- Check that you're a member of the group
- Ensure you own the resource you're trying to modify

### Not Found Errors (404)
```json
{
  "error_type": "not_found",
  "message": "Resource not found.",
  "status_code": 404
}
```

**Solutions:**
- Verify the ID is correct
- Check that the resource hasn't been deleted
- Use resolution tools to find correct IDs

### Validation Errors (400)
```json
{
  "error_type": "validation",
  "message": "Invalid request parameters.",
  "status_code": 400,
  "details": {
    "field": "cost",
    "value": "invalid"
  }
}
```

**Solutions:**
- Check parameter formats (dates, currency codes, etc.)
- Ensure required fields are provided
- Validate numeric ranges

### Rate Limit Errors (429)
```json
{
  "error_type": "rate_limit",
  "message": "Rate limit exceeded. Please try again later.",
  "status_code": 429
}
```

**Solutions:**
- Wait a few minutes before retrying
- Reduce frequency of API calls
- Use caching effectively

### Server Errors (500+)
```json
{
  "error_type": "server_error",
  "message": "Splitwise API error. Please try again.",
  "status_code": 500
}
```

**Solutions:**
- Retry the request after a short delay
- Check Splitwise API status
- Report persistent issues

---

## Common Patterns

### Creating a Simple Expense

```
1. "Create a $45 expense for dinner with Sarah"
   → Uses resolve-friend to find Sarah's user_id
   → Uses create-expense with split_equally=true
```

### Creating a Group Expense

```
1. "Create a $120 expense for groceries in my Roommates group"
   → Uses resolve-group to find group_id
   → Uses create-expense with the group_id
   → Automatically splits among all group members
```

### Finding and Updating an Expense

```
1. "Show me my recent expenses"
   → Uses get-expenses with dated_after filter
2. "Update expense 987654 to $60"
   → Uses update-expense with new cost
```

### Working with Categories

```
1. "What categories are available?"
   → Uses get-categories
2. "Create a $30 food expense"
   → Uses resolve-category to find "Food and drink" category_id
   → Uses create-expense with the category_id
```

### Managing Groups

```
1. "Create a trip group called 'Paris 2024'"
   → Uses create-group with group_type="trip"
2. "Add Mike to the Paris 2024 group"
   → Uses resolve-group to find group_id
   → Uses resolve-friend to find Mike's user_id
   → Uses add-user-to-group
```

### Natural Language Resolution

```
1. "Find my friend jon" (typo)
   → Uses resolve-friend with query="jon"
   → Returns matches for "John Smith" with high score
2. "Find group roomates" (typo)
   → Uses resolve-group with query="roomates"
   → Returns matches for "Roommates" with high score
```

---

## Best Practices

1. **Use Resolution Tools**: When working with names instead of IDs, always use the resolution tools (resolve-friend, resolve-group, resolve-category) for accurate matching.

2. **Handle Multiple Matches**: Resolution tools may return multiple matches. Present options to the user or use the highest-scoring match.

3. **Cache Static Data**: Categories and currencies are automatically cached. Don't call these tools repeatedly.

4. **Validate Before Creating**: Use get-categories and get-currencies to validate category IDs and currency codes before creating expenses.

5. **Check Balances**: Before removing users from groups, verify their balance is zero using get-group.

6. **Use Pagination**: When fetching large lists of expenses, use limit and offset parameters for pagination.

7. **Handle Errors Gracefully**: Always check for error responses and provide helpful feedback to users.

8. **Date Formats**: Always use ISO 8601 format for dates (e.g., "2024-01-15T19:30:00Z").

9. **Currency Codes**: Use three-letter uppercase currency codes (e.g., "USD", "EUR", "GBP").

10. **Decimal Precision**: Always use 2 decimal places for monetary amounts (e.g., "25.50", not "25.5").

---

For more information, see the [README](README.md) or visit the [Splitwise API Documentation](https://dev.splitwise.com/).
