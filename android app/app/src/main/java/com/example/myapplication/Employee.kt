package com.example.myapplication

import kotlinx.serialization.Serializable

@Serializable
data class Employee(
    val connection_mode: String,
    val public_url: String
)