terraform {
  backend "http" {
    address = "http://localhost:5000/outputs"

    lock_address = "http://localhost:5000/lock"
    lock_method = "POST"
    unlock_address = "http://localhost:5000/lock"
    unlock_method = "DELETE"
  }
}

output "test" {
  value = "test output"
}

