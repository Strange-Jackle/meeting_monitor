import xmlrpc.client
from typing import Optional
from app.modules.core.domain import LeadRepository, LeadCandidate
from app.core.config import settings

class OdooClient(LeadRepository):
    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self.common = None
        self.models = None
        self.uid = None
        
        # Set global socket timeout to prevent indefinite hanging on Odoo calls
        import socket
        socket.setdefaulttimeout(10.0)  # 10 seconds timeout

    def connect(self):
        if not self.uid:
            try:
                self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.url))
                self.uid = self.common.authenticate(self.db, self.username, self.password, {})
                self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.url))
                print(f"Connected to Odoo: {self.url} (UID: {self.uid})")
            except Exception as e:
                print(f"Failed to connect to Odoo: {e}")
                raise e

    def create_lead(self, lead: LeadCandidate) -> int:
        if not self.uid:
            self.connect()

        vals = {
            'name': f"Lead: {lead.name}",
            'contact_name': lead.name,
            'email_from': lead.email or "",
            'phone': lead.phone or "",
            'partner_name': lead.company or "",
            'description': f"{lead.notes}\n\nSource Summary: {lead.source_summary}"
        }

        try:
            lead_id = self.models.execute_kw(self.db, self.uid, self.password,
                'crm.lead', 'create', [vals])
            print(f"Created Odoo Lead ID: {lead_id}")
            return lead_id
        except Exception as e:
            print(f"Error creating lead in Odoo: {e}")
            raise e

if __name__ == "__main__":
    # Standalone Test
    print("Running standalone Odoo client test...")
    client = OdooClient()
    try:
        client.connect()
        dummy_lead = LeadCandidate(
            name="Test User 123",
            email="test1234@example.com",
            phone="1234567890",
            company="Test Company",
            notes="This is a test lead from the standalone script.",
            source_summary="Raw summary text goes here."
        )
        new_id = client.create_lead(dummy_lead)
        print(f"Test Successful! Created Lead ID: {new_id}")
    except Exception as e:
        print(f"Test Failed: {e}")
