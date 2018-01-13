#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvault
version_added: "2.5"
short_description: Manage Key Vault instance.
description:
    - Create, update and delete instance of Key Vault.

options:
    resource_group:
        description:
            - The name of the Resource Group to which the server belongs.
        required: True
    vault_name:
        description:
            - Name of the vault
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    tenant_id:
        description:
            - The Azure Active Directory tenant ID that should be used for authenticating requests to the key vault.
    sku:
        description:
            - SKU details
        suboptions:
            family:
                description:
                    - SKU family name
                required: True
            name:
                description:
                    - SKU name to specify whether the key vault is a standard vault or a premium vault.
                required: True
                choices:
                    - 'standard'
                    - 'premium'
    access_policies:
        description:
            - "An array of 0 to 16 identities that have access to the key vault. All identities in the array must use the same tenant ID as the key vault's t
              enant ID."
        type: list
        suboptions:
            tenant_id:
                description:
                    - The Azure Active Directory tenant ID that should be used for authenticating requests to the key vault.
                required: True
            object_id:
                description:
                    - "The object ID of a user, service principal or security group in the Azure Active Directory tenant for the vault. The object ID must be
                       unique for the list of access policies."
                required: True
            application_id:
                description:
                    -  Application ID of the client making request on behalf of a principal
            permissions:
                description:
                    - Permissions the identity has for keys, secrets and certificates.
                required: True
            keys:
                description:
                    - Permissions to keys
                type: list
            secrets:
                description:
                    - Permissions to secrets
                type: list
            certificates:
                description:
                    - Permissions to certificates
                type: list
            storage:
                description:
                    - Permissions to storage accounts
                type: list
    vault_uri:
        description:
            - The URI of the vault for performing operations on keys and secrets.
    enabled_for_deployment:
        description:
            - Property to specify whether Azure Virtual Machines are permitted to retrieve certificates stored as secrets from the key vault.
    enabled_for_disk_encryption:
        description:
            - Property to specify whether Azure Disk Encryption is permitted to retrieve secrets from the vault and unwrap keys.
    enabled_for_template_deployment:
        description:
            - Property to specify whether Azure Resource Manager is permitted to retrieve secrets from the key vault.
    enable_soft_delete:
        description:
            - Property to specify whether the C(soft delete) functionality is enabled for this key vault. It does not accept false value.
    create_mode:
        description:
            - "The vault's create mode to indicate whether the vault need to be recovered or not."
        choices:
            - 'recover'
            - 'default'

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) Key Vault
    azure_rm_keyvault:
      resource_group: NOT FOUND
      vault_name: NOT FOUND
      location: eastus
'''

RETURN = '''
id:
    description:
        - The Azure Resource Manager resource ID for the key vault.
    returned: always
    type: str
    sample: id
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.keyvault import KeyVaultManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMVaults(AzureRMModuleBase):
    """Configuration class for an Azure RM Key Vault resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            vault_name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            tenant_id=dict(
                type='str'
            ),
            sku=dict(
                type='dict'
            ),
            access_policies=dict(
                type='list'
            ),
            vault_uri=dict(
                type='str'
            ),
            enabled_for_deployment=dict(
                type='str'
            ),
            enabled_for_disk_encryption=dict(
                type='str'
            ),
            enabled_for_template_deployment=dict(
                type='str'
            ),
            enable_soft_delete=dict(
                type='str'
            ),
            create_mode=dict(
                type='str',
                choices=['recover',
                         'default']
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.vault_name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMVaults, self).__init__(derived_arg_spec=self.module_arg_spec,
                                            supports_check_mode=True,
                                            supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "tenant_id":
                    self.parameters.setdefault("properties", {})["tenant_id"] = kwargs[key]
                elif key == "sku":
                    self.parameters.setdefault("properties", {})["sku"] = kwargs[key]
                elif key == "access_policies":
                    self.parameters.setdefault("properties", {})["access_policies"] = kwargs[key]
                elif key == "vault_uri":
                    self.parameters.setdefault("properties", {})["vault_uri"] = kwargs[key]
                elif key == "enabled_for_deployment":
                    self.parameters.setdefault("properties", {})["enabled_for_deployment"] = kwargs[key]
                elif key == "enabled_for_disk_encryption":
                    self.parameters.setdefault("properties", {})["enabled_for_disk_encryption"] = kwargs[key]
                elif key == "enabled_for_template_deployment":
                    self.parameters.setdefault("properties", {})["enabled_for_template_deployment"] = kwargs[key]
                elif key == "enable_soft_delete":
                    self.parameters.setdefault("properties", {})["enable_soft_delete"] = kwargs[key]
                elif key == "create_mode":
                    self.parameters.setdefault("properties", {})["create_mode"] = kwargs[key]

        self.adjust_parameters()

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(KeyVaultManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_keyvault()

        if not old_response:
            self.log("Key Vault instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Key Vault instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Key Vault instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Key Vault instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_keyvault()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Key Vault instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_keyvault()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_keyvault():
                time.sleep(20)
        else:
            self.log("Key Vault instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def adjust_parameters(self):
        if self.parameters.get('access_policies', None) is not None:
        # option keys must go to dictionary :permissions as keys
        # option secrets must go to dictionary :permissions as secrets
        # option certificates must go to dictionary :permissions as certificates
        # option storage must go to dictionary :permissions as storage

    def rename_key(self, d, old_name, new_name):
        old_value = d.get(old_name, None)
        if old_value is not None:
            d.pop(old_name, None)
            d[new_name] = old_value

    def create_update_keyvault(self):
        '''
        Creates or updates Key Vault with the specified configuration.

        :return: deserialized Key Vault instance state dictionary
        '''
        self.log("Creating / Updating the Key Vault instance {0}".format(self.vault_name))

        try:
            response = self.mgmt_client.vaults.create_or_update(resource_group_name=self.resource_group,
                                                                vault_name=self.vault_name,
                                                                parameters=self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Key Vault instance.')
            self.fail("Error creating the Key Vault instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_keyvault(self):
        '''
        Deletes specified Key Vault instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Key Vault instance {0}".format(self.vault_name))
        try:
            response = self.mgmt_client.vaults.delete(resource_group_name=self.resource_group,
                                                      vault_name=self.vault_name)
        except CloudError as e:
            self.log('Error attempting to delete the Key Vault instance.')
            self.fail("Error deleting the Key Vault instance: {0}".format(str(e)))

        return True

    def get_keyvault(self):
        '''
        Gets the properties of the specified Key Vault.

        :return: deserialized Key Vault instance state dictionary
        '''
        self.log("Checking if the Key Vault instance {0} is present".format(self.vault_name))
        found = False
        try:
            response = self.mgmt_client.vaults.get(resource_group_name=self.resource_group,
                                                   vault_name=self.vault_name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Key Vault instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Key Vault instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMVaults()

if __name__ == '__main__':
    main()
