# -*- coding: utf-8 -*-

""" Sahana Eden Deployments Model

    @copyright: 2011-2013 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3DeploymentModel",
           "S3DeploymentAlertModel",
           ]

from gluon import *

from ..s3 import *

# =============================================================================
class S3DeploymentModel(S3Model):

    names = ["deploy_deployment",
             "deploy_deployment_id",
             "deploy_human_resource_assignment"]

    def model(self):

        T = current.T
        db = current.db
        define_table = self.define_table
        configure = self.configure
        super_link = self.super_link
        add_component = self.add_component

        s3 = current.response.s3
        crud_strings = s3.crud_strings
        
        # ---------------------------------------------------------------------
        # Deployment
        #
        tablename = "deploy_deployment"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             Field("title",
                                   #notnull=True,
                                   requires=IS_NOT_EMPTY()),
                             self.gis_location_id(
                                label = T("Country"),
                                widget = S3LocationAutocompleteWidget(level="L0"),
                                requires = IS_EMPTY_OR(IS_LOCATION(level="L0")),
                                represent = self.gis_LocationRepresent(sep=", "),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Country"),
                                                                T("Enter some characters to bring up a list of possible matches"))),
                             ),
                             Field("event_type"),        # @todo: replace by link
                             Field("status", "integer"), # @todo: lookup?
                             s3_comments(),
                             *s3_meta_fields())

        # Virtual field
        # @todo: move to real field wirtten onaccept?
        table.hrquantity = Field.Lazy(deploy_deployment_hrquantity)

        crud_form = S3SQLCustomForm("title",
                                    "location_id",
                                    "event_type",
                                    S3SQLInlineComponent("document",
                                                         name = "file",
                                                         label = T("Attachments"),
                                                         fields = ["file", "comments"],
                                    ),
                                    "comments",
                                    "created_on",
                                   )
        # Table configuration
        configure(tablename,
                  super_entity="doc_entity",
                  crud_form = crud_form,
                  list_fields = ["title",
                                 (T("Date"), "created_on"),
                                 (T("Country"), "location_id"),
                                 (T("Members"), "hrquantity")],
                  summary=[{"name": "rheader",
                            "common": True,
                            "widgets": [
                                {"method": self.add_button}
                            ]
                           },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}]
                            },
                            {"name": "map",
                             "label": "Map",
                             "widgets": [{"method": "map",
                                          "ajax_init": True}],
                            },
                  ],
                  filter_widgets = [
                      S3TextFilter("title",
                                   label=T("Search"),
                                  ),
                      S3LocationFilter("location_id",
                                       label=T("Location"),
                                       widget="multiselect",
                                       levels=["L0"],
                                       hidden=True,
                                      ),
                  ],
                  orderby="deploy_deployment.created_on desc",
                  delete_next=URL(c="deploy", f="deployment", args="summary"),
                 )

        # Components
        add_component("deploy_human_resource_assignment",
                      deploy_deployment="deployment_id")
        
        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_search = T("Search Deployments"),
            title_upload = T("Import Deployments"),
            subtitle_create = T("Add New Deployment"),
            label_list_button = T("List Deployments"),
            label_create_button = T("New Deployment"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))
                
        # Reusable field
        represent = S3Represent(lookup=tablename, fields=["title"])
        deployment_id = S3ReusableField("deployment_id", table,
                                        requires = IS_ONE_OF(db,
                                                             "deploy_deployment.id",
                                                             represent),
                                        represent = represent,
                                        label = T("Deployment"),
                                        ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Deployment of human resources
        #
        tablename = "deploy_human_resource_assignment"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             deployment_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             s3_date("start_date",
                                     label = T("Start Date")),
                             s3_date("end_date",
                                     label = T("End Date")),
                             *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  super_entity="doc_entity")

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Assignment"),
            title_display = T("Assignment Details"),
            title_list = T("Assignments"),
            title_update = T("Edit Assignment Details"),
            title_search = T("Search Assignments"),
            title_upload = T("Import Assignments"),
            subtitle_create = T("Add New Assignment"),
            label_list_button = T("List Assignments"),
            label_create_button = T("Add Assignment"),
            label_delete_button = T("Delete Assignment"),
            msg_record_created = T("Assignment added"),
            msg_record_modified = T("Assignment Details updated"),
            msg_record_deleted = T("Assignment deleted"),
            msg_list_empty = T("No Assignments currently registered"))

        # ---------------------------------------------------------------------
        # Deployment of assets
        #
        # @todo: deploy_asset_assignment
        
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(deploy_deployment_id = deployment_id)

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        deployment_id = S3ReusableField("deployment_id", "integer",
                                        readable=False, writable=False)
        return dict(deploy_deployment_id = deployment_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def add_button(r, widget_id=None, visible=True, **attr):

        return A(S3Method.crud_string(r.tablename,
                                      "label_create_button"),
                 _href=r.url(method="create", id=0, vars={}),
                 _class="action-btn",
                )
                
# =============================================================================
class S3DeploymentAlertModel(S3Model):

    names = ["deploy_alert",
             "deploy_group",
             "deploy_response"]

    def model(self):

        T = current.T

        define_table = self.define_table
        super_link = self.super_link
        configure = self.configure
        add_component = self.add_component

        # ---------------------------------------------------------------------
        # Alert (also the PE representing its Recipients)
        #
        tablename = "deploy_alert"
        table = define_table(tablename,
                             self.deploy_deployment_id(),
                             super_link("pe_id", "pr_pentity"),
                             # @todo: link to alert message
                             *s3_meta_fields())

        # Table Configuration
        configure(tablename,
                  super_entity="pr_pentity")

        # Components
        add_component("deploy_alert_recipient",
                      deploy_alert="alert_id")

        # Reusable field
        represent = S3Represent(lookup=tablename)
        alert_id = S3ReusableField("alert_id", table,
                                   requires = IS_ONE_OF(db,
                                                        "deploy_alert.id",
                                                        represent),
                                   represent = represent,
                                   label = T("Alert"),
                                   ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Recipient of the Alert
        #
        tablename = "deploy_alert_recipient"
        table = define_table(tablename,
                             alert_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Responses to Alerts
        #
        tablename = "deploy_response"
        table = define_table(tablename,
                             self.deploy_deployment_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             # @todo: link to response message
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        return dict()

# =============================================================================
def deploy_deployment_hrquantity(row):
    """ Number of human resources deployed """

    if hasattr(row, "deploy_deployment"):
        row = row.deploy_deployment
    try:
        deployment_id = row.id
    except AttributeError:
        return 0

    db = current.db
    table = db.deploy_human_resource_assignment
    count = table.id.count()
    row = db(table.deployment_id == deployment_id).select(count).first()
    if row:
        return row[count]
    else:
        return 0

# END =========================================================================
