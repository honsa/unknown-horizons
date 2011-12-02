# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from horizons.world.resourcehandler import StorageResourceHandler
from horizons.world.building.collectingbuilding import CollectingBuilding
from horizons.gui.tabs import BranchOfficeOverviewTab, BuySellTab, InventoryTab, \
		 MainSquareOverviewTab, AccountTab, \
		 MainSquareSailorsTab, MainSquarePioneersTab, MainSquareSettlersTab, \
		 EnemyBranchOfficeOverviewTab, ProductionOverviewTab
from building import BasicBuilding, SelectableBuilding
from buildable import BuildableSingle, BuildableSingleFromShip
from horizons.world.building.buildingresourcehandler import ProducerBuilding
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.building.production import SettlerServiceProvider
from horizons.world.building.path import Path
from horizons.world.production.producer import Producer

class StorageBuilding(SelectableBuilding, StorageResourceHandler, \
                      CollectingBuilding, BasicBuilding):
	"""Building that gets pickups and provides them for anyone.
	Inherited eg. by branch office, storage tent.
	These objects don't have a storage themselves, but use the settlement storage.
	"""
	tabs = (BranchOfficeOverviewTab, InventoryTab, AccountTab)
	has_own_inventory = False # we share island inventory
	def __init__(self, x, y, owner, instance = None, **kwargs):
		super(StorageBuilding, self).__init__(x = x, y = y, owner = owner, instance = instance, **kwargs)

	def initialize(self):
		super(StorageBuilding, self).initialize()

		# Only don't add for mainsquare
		if self.id is not 4:
			self.get_component(StorageComponent).inventory = self.settlement.get_component(StorageComponent).inventory
		self.get_component(StorageComponent).inventory.add_change_listener(self._changed)
		self.get_component(StorageComponent).inventory.adjust_limit(self.session.db.get_storage_building_capacity(self.id))

	def remove(self):
		# this shouldn't be absolutely necessary since the changelistener uses weak references
		self.get_component(StorageComponent).inventory.remove_change_listener(self._changed)
		self.owner_inventory.discard_change_listener(self._changed)

		self.get_component(StorageComponent).inventory.adjust_limit(-self.session.db.get_storage_building_capacity(self.id))
		super(StorageBuilding, self).remove()

	def get_utilisation_history_length(self):
		return None if not self.get_local_collectors() else self.get_local_collectors()[0].get_utilisation_history_length()

	def get_collector_utilisation(self):
		collectors = self.get_local_collectors()
		if not collectors:
			return None
		return sum(collector.get_utilisation() for collector in collectors) / float(len(collectors))

class StorageTent(StorageBuilding, BuildableSingle):
	"""Can't inherit from Buildable* in StorageBuilding because of mro issues."""
	pass

class BranchOffice(StorageBuilding, BuildableSingleFromShip):
	tearable = False
	tabs = (BranchOfficeOverviewTab, InventoryTab, BuySellTab, AccountTab)
	enemy_tabs = (EnemyBranchOfficeOverviewTab,)
	def __init__(self, *args, **kwargs):
		super(BranchOffice, self).__init__(*args, **kwargs)
		self.settlement.branch_office = self # we never need to unset this since bo's are indestructible
		# settlement branch office setting is done at the settlement for loading

class MainSquare(Path, StorageBuilding, SettlerServiceProvider):
	walkable = True
	tabs = (MainSquareOverviewTab, ProductionOverviewTab, InventoryTab, AccountTab, MainSquareSailorsTab, MainSquarePioneersTab, MainSquareSettlersTab)

	def recalculate_orientation(self):
		# change gfx according to roads here
		pass

	def _load_provided_resources(self):
		"""Storages provide every res.
		"""
		return self.session.db.get_res(only_tradeable=False)
