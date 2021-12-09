
FILE_UPLOAD_INVOICE_CREATE = """
mutation newUploadInvoices($input: FileUploadInvoicesCreateInput!) {
  fileUploadInvoiceCreate(input: $input) {
    errors {
      message
    }
    fileUploadInvoices {
      created
      total
    }
  }
}
"""
