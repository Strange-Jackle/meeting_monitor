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

    def get_stage_id(self, stage_name: str) -> Optional[int]:
        """Get stage ID by name from CRM stages."""
        try:
            if not self.uid:
                self.connect()
            
            # Search for stage by name
            stage_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'crm.stage', 'search',
                [[['name', 'ilike', stage_name]]]
            )
            return stage_ids[0] if stage_ids else None
        except Exception as e:
            print(f"Error finding stage '{stage_name}': {e}")
            return None

    def create_lead(self, lead: LeadCandidate, starred_hints: Optional[list] = None, sentiment_score: int = 50) -> int:
        """
        Create a lead in Odoo CRM with stage based on sentiment score.
        
        Args:
            lead: Lead data
            starred_hints: List of important hints from meeting
            sentiment_score: Score 0-100, determines stage:
                            >= 50 = Qualified
                            < 50 = Lost
        """
        if not self.uid:
            self.connect()

        description = f"{lead.notes}\n\nSource Summary: {lead.source_summary}"
        
        # Append Starred Hints if any
        if starred_hints:
            hints_text = "\n".join([f"- ⭐ {hint}" for hint in starred_hints])
            description += f"\n\n=== STARRED HINTS ===\n{hints_text}"
        
        # Add sentiment info
        if sentiment_score >= 50:
            qualification = "✅ QUALIFIED"
            stage_name = "Qualified"
        else:
            qualification = "❌ LOST"
            stage_name = "Lost"
        
        description += f"\n\n=== SENTIMENT ANALYSIS ===\nScore: {sentiment_score}/100\nResult: {qualification}"

        vals = {
            'name': f"Lead: {lead.name}",
            'contact_name': lead.name,
            'email_from': lead.email or "",
            'phone': lead.phone or "",
            'partner_name': lead.company or "",
            'description': description
        }
        
        # Try to set stage based on sentiment
        stage_id = self.get_stage_id(stage_name)
        if stage_id:
            vals['stage_id'] = stage_id
            print(f"[Odoo] Setting lead stage to: {stage_name} (ID: {stage_id})")

        try:
            lead_id = self.models.execute_kw(self.db, self.uid, self.password,
                'crm.lead', 'create', [vals])
            print(f"Created Odoo Lead ID: {lead_id} with stage: {stage_name}")
            return lead_id
        except Exception as e:
            print(f"Error creating lead in Odoo: {e}")
            raise e

    def update_lead_stage(self, lead_id: int, sentiment_score: int) -> bool:
        """
        Update an existing lead's stage based on sentiment score.
        
        Args:
            lead_id: Odoo lead ID
            sentiment_score: Score 0-100
        
        Returns:
            True if updated successfully
        """
        try:
            if not self.uid:
                self.connect()
            
            stage_name = "Qualified" if sentiment_score >= 50 else "Lost"
            stage_id = self.get_stage_id(stage_name)
            
            if stage_id:
                self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'crm.lead', 'write',
                    [[lead_id], {'stage_id': stage_id}]
                )
                print(f"[Odoo] Updated lead {lead_id} stage to: {stage_name}")
                return True
            return False
        except Exception as e:
            print(f"[Odoo] Error updating lead stage: {e}")
            return False

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
