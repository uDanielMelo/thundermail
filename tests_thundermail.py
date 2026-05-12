"""
=============================================================================
Testes Unitários – ThunderMail
=============================================================================
Telas cobertas (16 no total):
 1.  index               – Página inicial / redirecionamento
 2.  cadastro            – Registro de novo usuário
 3.  login_view          – Autenticação
 4.  logout_view         – Encerrar sessão
 5.  dashboard           – Painel principal
 6.  configuracoes       – Configurações da conta
 7.  membros             – Membros da organização
 8.  campaigns_list      – Lista de campanhas
 9.  campaign_create     – Criar campanha
10.  campaign_detail     – Detalhe de campanha
11.  contacts_list       – Lista de contatos / grupos
12.  group_create        – Criar grupo de contatos
13.  tasks_home          – Home de tarefas (redireciona para kanban)
14.  project_create      – Criar projeto
15.  documents_home      – Home de documentos
16.  contracts_list      – Lista de contratos
=============================================================================
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import (
    User, Organization, OrganizationMember, UserSettings, MemberPermission
)
from apps.campaigns.models import Campaign
from apps.contacts.models import ContactGroup, Contact
from apps.tasks.models import Project, Task
from apps.contracts.models import Contract
from apps.documents.models import Document, Folder


# ---------------------------------------------------------------------------
# Helper base – cria usuário + organização + membership em um só lugar
# ---------------------------------------------------------------------------

class BaseTestCase(TestCase):
    """
    Configura um usuário administrador com organização vinculada
    e um Client já autenticado, reutilizável em todos os testes.
    """

    def setUp(self):
        self.client = Client()

        # Usuário admin
        self.user = User.objects.create_user(
            username="admin@teste.com",
            email="admin@teste.com",
            password="Senha@1234",
            first_name="Admin Teste",
        )

        # Organização
        self.org = Organization.objects.create(
            nome="Org Teste",
            tipo="pf",
            email="org@teste.com",
        )

        # Membership admin
        self.membership = OrganizationMember.objects.create(
            organization=self.org,
            user=self.user,
            role="admin",
            status="active",
        )

        # Permissões (necessário para views com @require_permission)
        MemberPermission.objects.create(
            member=self.membership,
            email_marketing=True,
            contacts=True,
            scheduling=True,
            analytics=True,
            integrations=True,
        )

        # Login
        self.client.login(username="admin@teste.com", password="Senha@1234")


# =============================================================================
# 1. TELA: index
# =============================================================================

class IndexViewTest(TestCase):
    """Tela inicial – redireciona usuário autenticado para o dashboard."""

    def setUp(self):
        self.client = Client()

    def test_index_usuario_nao_autenticado_renderiza_landing(self):
        """Visitante anônimo vê a landing page (status 200)."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_index_usuario_autenticado_redireciona_dashboard(self):
        """Usuário logado é redirecionado para o dashboard."""
        user = User.objects.create_user(
            username="u@teste.com", email="u@teste.com", password="Abc@1234"
        )
        self.client.login(username="u@teste.com", password="Abc@1234")
        response = self.client.get(reverse("index"))
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)


# =============================================================================
# 2. TELA: cadastro
# =============================================================================

class CadastroViewTest(TestCase):
    """Tela de cadastro de novo usuário."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("accounts:cadastro")

    def test_get_exibe_formulario(self):
        """GET retorna o template de cadastro com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/cadastro.html")

    def test_post_cria_usuario_e_redireciona(self):
        """POST com dados válidos cria usuário, organização e redireciona para login."""
        dados = {
            "tipo": "pf",
            "nome": "Novo Usuario",
            "email": "novo@teste.com",
            "password": "Senha@123",
            "password2": "Senha@123",
            "telefone": "11999999999",
            "cpf": "123.456.789-00",
        }
        response = self.client.post(self.url, dados)
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="novo@teste.com").exists())
        self.assertTrue(Organization.objects.filter(email="novo@teste.com").exists())

    def test_post_senhas_diferentes_exibe_erro(self):
        """Senhas divergentes impedem o cadastro e exibem mensagem de erro."""
        dados = {
            "tipo": "pf",
            "nome": "Erro",
            "email": "erro@teste.com",
            "password": "Senha@123",
            "password2": "SenhaDiferente",
        }
        response = self.client.post(self.url, dados)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="erro@teste.com").exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("senhas" in str(m).lower() for m in messages))

    def test_post_email_duplicado_exibe_erro(self):
        """E-mail já cadastrado exibe mensagem de erro sem criar novo usuário."""
        User.objects.create_user(
            username="dup@teste.com", email="dup@teste.com", password="Abc@1234"
        )
        dados = {
            "tipo": "pf",
            "nome": "Dup",
            "email": "dup@teste.com",
            "password": "Abc@1234",
            "password2": "Abc@1234",
        }
        response = self.client.post(self.url, dados)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="dup@teste.com").count(), 1)


# =============================================================================
# 3. TELA: login
# =============================================================================

class LoginViewTest(TestCase):
    """Tela de autenticação."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            username="login@teste.com", email="login@teste.com", password="Abc@1234"
        )

    def test_get_exibe_formulario_de_login(self):
        """GET retorna o template de login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_post_credenciais_validas_redireciona_dashboard(self):
        """Login bem-sucedido redireciona para o dashboard."""
        response = self.client.post(self.url, {"email": "login@teste.com", "password": "Abc@1234"})
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_post_credenciais_invalidas_exibe_erro(self):
        """Credenciais incorretas mantêm o usuário na tela de login com mensagem."""
        response = self.client.post(self.url, {"email": "login@teste.com", "password": "ERRADA"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("incorretos" in str(m).lower() or "senha" in str(m).lower() for m in messages))


# =============================================================================
# 4. TELA: logout
# =============================================================================

class LogoutViewTest(BaseTestCase):
    """Tela de encerramento de sessão."""

    def test_logout_redireciona_para_login(self):
        """Após logout o usuário é redirecionado para a tela de login."""
        response = self.client.get(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)

    def test_logout_encerra_sessao(self):
        """Após logout o usuário não consegue acessar área restrita sem relogar."""
        self.client.get(reverse("accounts:logout"))
        response = self.client.get(reverse("dashboard"))
        # Deve redirecionar para login (usuário deslogado)
        self.assertEqual(response.status_code, 302)


# =============================================================================
# 5. TELA: dashboard
# =============================================================================

class DashboardViewTest(BaseTestCase):
    """Painel principal (requer autenticação)."""

    def test_dashboard_retorna_200_para_usuario_autenticado(self):
        """Usuário logado vê o dashboard com status 200."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")

    def test_dashboard_redireciona_usuario_nao_autenticado(self):
        """Usuário anônimo é redirecionado para o login."""
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_dashboard_contexto_contem_chaves_esperadas(self):
        """O contexto do dashboard deve conter as chaves de dados principais."""
        response = self.client.get(reverse("dashboard"))
        chaves_esperadas = [
            "total_campaigns", "total_contacts", "total_sent",
            "recent_campaigns", "projects_data", "contracts_pending",
        ]
        for chave in chaves_esperadas:
            self.assertIn(chave, response.context, msg=f"Chave ausente no contexto: {chave}")


# =============================================================================
# 6. TELA: configuracoes
# =============================================================================

class ConfiguracoesViewTest(BaseTestCase):
    """Tela de configurações da conta."""

    def setUp(self):
        super().setUp()
        self.url = reverse("accounts:configuracoes")

    def test_get_exibe_pagina_de_configuracoes(self):
        """GET retorna a tela de configurações com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/configuracoes.html")

    def test_post_salva_nome_remetente(self):
        """POST atualiza o nome do remetente e redireciona."""
        response = self.client.post(self.url, {"nome_remetente": "Minha Empresa"})
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        settings_obj = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings_obj.nome_remetente, "Minha Empresa")

    def test_contexto_contem_org_e_membros(self):
        """O contexto deve incluir a organização e os membros."""
        response = self.client.get(self.url)
        self.assertIn("org", response.context)
        self.assertIn("members", response.context)


# =============================================================================
# 7. TELA: membros
# =============================================================================

class MembrosViewTest(BaseTestCase):
    """Tela de gerenciamento de membros da organização."""

    def setUp(self):
        super().setUp()
        self.url = reverse("accounts:membros")

    def test_get_exibe_pagina_de_membros(self):
        """GET retorna a lista de membros com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/membros.html")

    def test_contexto_contem_membros_da_org(self):
        """O contexto deve listar membros pertencentes à organização do usuário."""
        response = self.client.get(self.url)
        self.assertIn("members", response.context)
        emails = [m.user.email for m in response.context["members"]]
        self.assertIn(self.user.email, emails)

    def test_nao_autenticado_redireciona(self):
        """Usuário não autenticado é redirecionado para o login."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# =============================================================================
# 8. TELA: campaigns_list
# =============================================================================

class CampaignsListViewTest(BaseTestCase):
    """Tela de listagem de campanhas."""

    def setUp(self):
        super().setUp()
        self.url = reverse("campaigns:list")
        Campaign.objects.create(
            organization=self.org,
            user=self.user,
            name="Campanha Teste",
            subject="Assunto",
            status="rascunho",
        )

    def test_get_exibe_lista_de_campanhas(self):
        """GET retorna a lista de campanhas com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaigns/list.html")

    def test_contexto_contem_campanhas_da_org(self):
        """O contexto deve incluir as campanhas da organização."""
        response = self.client.get(self.url)
        self.assertIn("campaigns", response.context)
        nomes = [c.name for c in response.context["campaigns"]]
        self.assertIn("Campanha Teste", nomes)

    def test_busca_por_nome_filtra_resultados(self):
        """O parâmetro 'q' deve filtrar campanhas pelo nome."""
        Campaign.objects.create(
            organization=self.org, user=self.user,
            name="Outra Campanha", status="rascunho"
        )
        response = self.client.get(self.url, {"q": "Campanha Teste"})
        nomes = [c.name for c in response.context["campaigns"]]
        self.assertIn("Campanha Teste", nomes)
        self.assertNotIn("Outra Campanha", nomes)


# =============================================================================
# 9. TELA: campaign_create
# =============================================================================

class CampaignCreateViewTest(BaseTestCase):
    """Tela de criação de campanha."""

    def setUp(self):
        super().setUp()
        self.url = reverse("campaigns:create")
        self.group = ContactGroup.objects.create(organization=self.org, name="Grupo A")

    def test_get_exibe_formulario_de_criacao(self):
        """GET retorna o formulário de criação com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaigns/create.html")

    def test_post_sem_campos_obrigatorios_exibe_erro(self):
        """POST sem nome, assunto ou corpo não cria campanha."""
        contagem_antes = Campaign.objects.filter(organization=self.org).count()
        response = self.client.post(self.url, {"name": "", "subject": "", "body": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Campaign.objects.filter(organization=self.org).count(), contagem_antes)

    def test_post_valido_cria_campanha_como_rascunho(self):
        """POST com dados válidos cria a campanha no status 'rascunho'."""
        dados = {
            "name": "Nova Campanha",
            "subject": "Olá mundo",
            "body": "<p>Conteúdo</p>",
            "group": self.group.pk,
            "action": "save",
            "reply_to": "",
        }
        self.client.post(self.url, dados)
        self.assertTrue(Campaign.objects.filter(name="Nova Campanha", organization=self.org).exists())
        camp = Campaign.objects.get(name="Nova Campanha", organization=self.org)
        self.assertEqual(camp.status, "rascunho")


# =============================================================================
# 10. TELA: campaign_detail
# =============================================================================

class CampaignDetailViewTest(BaseTestCase):
    """Tela de detalhe de uma campanha."""

    def setUp(self):
        super().setUp()
        self.campaign = Campaign.objects.create(
            organization=self.org,
            user=self.user,
            name="Campanha Detalhe",
            subject="Assunto",
            status="rascunho",
        )
        self.url = reverse("campaigns:detail", kwargs={"pk": self.campaign.pk})

    def test_get_exibe_detalhe_da_campanha(self):
        """GET retorna os detalhes da campanha com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaigns/detail.html")

    def test_campanha_de_outra_org_retorna_404(self):
        """Campanha de outra organização deve retornar 404."""
        outra_org = Organization.objects.create(nome="Org B", tipo="pf")
        outro_user = User.objects.create_user(
            username="outro@b.com", email="outro@b.com", password="Abc@1234"
        )
        OrganizationMember.objects.create(
            organization=outra_org, user=outro_user, role="admin", status="active"
        )
        campanha_alheia = Campaign.objects.create(
            organization=outra_org, user=outro_user,
            name="Alheia", status="rascunho"
        )
        url_alheia = reverse("campaigns:detail", kwargs={"pk": campanha_alheia.pk})
        response = self.client.get(url_alheia)
        self.assertEqual(response.status_code, 404)


# =============================================================================
# 11. TELA: contacts_list
# =============================================================================

class ContactsListViewTest(BaseTestCase):
    """Tela de listagem de contatos e grupos."""

    def setUp(self):
        super().setUp()
        self.url = reverse("contacts:list")
        self.group = ContactGroup.objects.create(organization=self.org, name="Grupo Contatos")
        Contact.objects.create(organization=self.org, email="contato@teste.com", name="Contato Um")

    def test_get_retorna_status_200(self):
        """GET retorna a lista de contatos com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contacts/list.html")

    def test_contexto_contem_grupos(self):
        """O contexto deve listar grupos da organização."""
        response = self.client.get(self.url)
        self.assertIn("groups", response.context)
        nomes = [g.name for g in response.context["groups"]]
        self.assertIn("Grupo Contatos", nomes)

    def test_nao_autenticado_redireciona(self):
        """Usuário não autenticado é bloqueado."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# =============================================================================
# 12. TELA: group_create
# =============================================================================

class GroupCreateViewTest(BaseTestCase):
    """Tela de criação de grupo de contatos."""

    def setUp(self):
        super().setUp()
        self.url = reverse("contacts:group_create")

    def test_post_cria_grupo_e_redireciona(self):
        """POST com nome e e-mails válidos cria o grupo e redireciona para contacts_list."""
        response = self.client.post(self.url, {
            "name": "Grupo Novo",
            "notes": "",
            "emails": "contato1@teste.com\ncontato2@teste.com",
        })
        self.assertRedirects(response, reverse("contacts:list"), fetch_redirect_response=False)
        self.assertTrue(ContactGroup.objects.filter(name="Grupo Novo", organization=self.org).exists())

    def test_post_sem_nome_nao_cria_grupo(self):
        """POST sem nome não cria o grupo."""
        contagem_antes = ContactGroup.objects.filter(organization=self.org).count()
        self.client.post(self.url, {"name": "", "notes": "", "emails": "x@teste.com"})
        self.assertEqual(ContactGroup.objects.filter(organization=self.org).count(), contagem_antes)

    def test_nao_autenticado_redireciona(self):
        """Usuário não autenticado é bloqueado."""
        self.client.logout()
        response = self.client.post(self.url, {"name": "X"})
        self.assertEqual(response.status_code, 302)


# =============================================================================
# 13. TELA: tasks_home
# =============================================================================

class TasksHomeViewTest(BaseTestCase):
    """Tela home de tarefas."""

    def setUp(self):
        super().setUp()
        self.url = reverse("tasks:home")

    def test_sem_projetos_renderiza_tela_vazia(self):
        """Sem projetos, a home exibe a tela de tarefas com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/home.html")

    def test_com_projetos_redireciona_para_kanban(self):
        """Com projetos existentes, redireciona para o detalhe do primeiro."""
        projeto = Project.objects.create(
            organization=self.org, user=self.user, name="Projeto Alpha"
        )
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("tasks:project_detail", kwargs={"pk": projeto.pk}),
            fetch_redirect_response=False,
        )

    def test_nao_autenticado_redireciona(self):
        """Usuário não autenticado é bloqueado."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# =============================================================================
# 14. TELA: project_create
# =============================================================================

class ProjectCreateViewTest(BaseTestCase):
    """Tela de criação de projeto."""

    def setUp(self):
        super().setUp()
        self.url = reverse("tasks:project_create")

    def test_post_cria_projeto_e_redireciona_para_kanban(self):
        """POST com nome válido cria o projeto e redireciona para o kanban."""
        response = self.client.post(self.url, {"name": "Projeto Beta", "color": "#1D9E75"})
        self.assertTrue(Project.objects.filter(name="Projeto Beta", organization=self.org).exists())
        projeto = Project.objects.get(name="Projeto Beta")
        self.assertRedirects(
            response,
            reverse("tasks:project_detail", kwargs={"pk": projeto.pk}),
            fetch_redirect_response=False,
        )

    def test_post_sem_nome_exibe_erro(self):
        """POST sem nome exibe mensagem de erro e não cria projeto."""
        contagem_antes = Project.objects.filter(organization=self.org).count()
        response = self.client.post(self.url, {"name": "", "color": "#378ADD"})
        self.assertRedirects(response, reverse("tasks:home"), fetch_redirect_response=False)
        self.assertEqual(Project.objects.filter(organization=self.org).count(), contagem_antes)

    def test_get_retorna_405_metodo_nao_permitido(self):
        """GET na rota que só aceita POST retorna 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


# =============================================================================
# 15. TELA: documents_home
# =============================================================================

class DocumentsHomeViewTest(BaseTestCase):
    """Tela home de documentos."""

    def setUp(self):
        super().setUp()
        self.url = reverse("documents:home")

    def test_get_retorna_status_200(self):
        """GET retorna a home de documentos com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "documents/home.html")

    def test_contexto_contem_chaves_esperadas(self):
        """O contexto deve incluir documentos, pastas e tags."""
        response = self.client.get(self.url)
        for chave in ["documents", "folders", "tags"]:
            self.assertIn(chave, response.context, msg=f"Chave ausente: {chave}")

    def test_filtro_favoritos(self):
        """O filtro 'favorites=1' deve retornar apenas documentos favoritos."""
        Document.objects.create(user=self.user, title="Favorito", doc_type="note", is_favorite=True)
        Document.objects.create(user=self.user, title="Normal", doc_type="note", is_favorite=False)
        response = self.client.get(self.url, {"favorites": "1"})
        titulos = [d.title for d in response.context["documents"]]
        self.assertIn("Favorito", titulos)
        self.assertNotIn("Normal", titulos)

    def test_nao_autenticado_redireciona(self):
        """Usuário não autenticado é bloqueado."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# =============================================================================
# 16. TELA: contracts_list
# =============================================================================

class ContractsListViewTest(BaseTestCase):
    """Tela de listagem de contratos."""

    def setUp(self):
        super().setUp()
        self.url = reverse("contracts:list")

    def test_get_retorna_status_200(self):
        """GET retorna a lista de contratos com status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contracts/list.html")

    def test_contexto_lista_contratos_do_usuario(self):
        """A listagem mostra apenas contratos do usuário autenticado."""
        Contract.objects.create(user=self.user, title="Contrato A")
        outro_user = User.objects.create_user(
            username="outro@c.com", email="outro@c.com", password="Abc@1234"
        )
        Contract.objects.create(user=outro_user, title="Contrato Alheio")
        response = self.client.get(self.url)
        titulos = [c.title for c in response.context["contracts"]]
        self.assertIn("Contrato A", titulos)
        self.assertNotIn("Contrato Alheio", titulos)

    def test_nao_autenticado_redireciona(self):
        """Usuário não autenticado é bloqueado."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
