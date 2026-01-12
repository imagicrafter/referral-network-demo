"""
Referral Network Demo - Shared source code.
This package contains shared modules used across CLI, Azure Functions, and Gradient agents.
"""
from src.cosmos_connection import get_client, execute_query

__all__ = ['get_client', 'execute_query']
