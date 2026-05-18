# Repository vs Active Record — the architectural pattern comparison

## Source / Origin
- The "DDD or pragmatic?" interview question. Often surfaces in NestJS, Spring, Hibernate, Sequelize discussions.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md`, `02-orm-comparison.md` (AR vs DM section).

## Why this question matters in interviews
The architectural pattern your ORM nudges you toward shapes the entire codebase. Active Record (Sequelize, ActiveRecord, Eloquent) is fast-to-ship; Repository / Data Mapper (Hibernate, SQLAlchemy, TypeORM Repository, Doctrine) is testable and clean for complex domains. Senior candidates **articulate the trade-off** rather than picking a side, and call out which ORMs blur the line (TypeORM dual-mode, Prisma's repository-like design).

## Concepts involved

### The two patterns at a glance

```
   ACTIVE RECORD                                  DATA MAPPER / REPOSITORY
   ──────────────                                 ────────────────────────

   class User extends Model {                     class User {                    ◄── pure domain
     name: string;                                  name: string;
     async save() { ... }                         }
     async delete() { ... }                       class UserRepository {           ◄── persistence
     static async findById(...) { ... }             save(u: User) { ... }
   }                                                delete(u: User) { ... }
                                                    findById(id) { ... }
   const u = await User.findById(1);              }
   u.name = 'A'; await u.save();
                                                  const u = await userRepo.findById(1);
                                                  u.name = 'A'; await userRepo.save(u);

   Pros: minimal boilerplate; fast.               Pros: testable; domain is pure.
   Cons: domain coupled to DB.                    Cons: more code; steeper learning.
```

### Syntax — same operation, two styles

```typescript
// ============================================================
// Active Record (Sequelize)
// ============================================================
const u = await User.findByPk(1);
u.email = 'new@x.com';
await u.save();
await u.destroy();

// Class method
const all = await User.findAll({ where: { active: true } });

// ============================================================
// Data Mapper / Repository (TypeORM)
// ============================================================
const userRepo = ds.getRepository(User);
const u = await userRepo.findOneByOrFail({ id: 1 });
u.email = 'new@x.com';
await userRepo.save(u);
await userRepo.delete({ id: 1 });

// Custom repository
@EntityRepository(User)
class UserRepository extends Repository<User> {
  findActive() { return this.find({ where: { active: true } }); }
  findByOrg(orgId: number) { return this.find({ where: { orgId } }); }
}

// ============================================================
// Hibernate / JPA — Data Mapper via EntityManager
// ============================================================
@Repository
public class UserRepository {
  @PersistenceContext EntityManager em;
  public User findById(Long id) { return em.find(User.class, id); }
  public void save(User u) { em.persist(u); }
}

// ============================================================
// Prisma — repository-like, but with the entity-class step skipped
// ============================================================
const u = await prisma.user.findUniqueOrThrow({ where: { id: 1 } });
await prisma.user.update({ where: { id: 1 }, data: { email: 'new@x.com' } });
// `prisma.user` is essentially a generated UserRepository.
```

### Edge cases / interview traps

1. **Implicit global session in AR.** `User.findById(1)` uses a hidden global connection; testing without that global is painful.
2. **Coupling.** `class User` knows about the database in AR. Reusing the model outside a DB context (a CLI tool, a worker) requires bootstrapping the ORM.
3. **Hybrid mode in TypeORM.** Both `userRepo.save(u)` and `u.save()` work, depending on whether you extend `BaseEntity`. Teams should pick one to avoid drift.
4. **Static methods vs DI.** AR static `User.findAll()` is hard to dependency-inject; DM repository can be passed in.
5. **Custom finders.** AR puts them on the class as static methods. DM puts them on the repository — usually cleaner.
6. **Aggregates and complex invariants** (DDD) — AR struggles because the persister doesn't know about aggregate boundaries; DM lets you express them.
7. **Cascading saves.** AR usually doesn't cascade automatically; DM's session pattern (Hibernate, SQLAlchemy) does.
8. **Active Record + transactions.** Each `u.save()` is its own TX by default; composing multiple becomes awkward. DM with explicit `manager` / `session` is cleaner.
9. **Mocking for tests.** Mocking a class method `User.findById` is gross; mocking `userRepo.findById` is trivial.

## Mental Model

```
   Active Record:                          Data Mapper (Repository):

   ┌────────────────────────┐              ┌──────────────────────────┐
   │  class User extends    │              │  class User              │   pure domain
   │  Model {               │              │  (no save/find)          │
   │   save(), find()       │              └──────────┬───────────────┘
   │   findById(...)        │                         │  used by
   └────────────┬───────────┘                         ▼
                │                          ┌──────────────────────────┐
                │ uses                     │  class UserRepository    │   persistence
                ▼                          │   save(u), findById(...) │
   ┌────────────────────────┐              └──────────┬───────────────┘
   │ implicit global        │                         │
   │ DB / session           │                         │ uses
   └────────────────────────┘                         ▼
                                           ┌──────────────────────────┐
                                           │ explicit Session / DB    │
                                           └──────────────────────────┘
```

Active Record's strength: simplicity, fewer files. Data Mapper's strength: domain stays a pure object graph; persistence is pluggable.

## Why interviewers care

- Tests **architectural vocabulary**: AR, DM, Repository, Unit of Work, Identity Map.
- Tests **judgement** about codebase complexity vs ship speed.
- Catches the candidate who's only used one style and can't articulate why the other exists.

## Common beginner confusion

- **"Active Record is bad."** Wrong — for CRUD-heavy small/medium apps, it ships 2-3x faster. Rails ate the world with it.
- **"Repository is just wrapping every ORM call in a class."** It is — but the wrapping enables: testing (mock the repo), domain purity (entities don't know about persistence), composition (services orchestrate multiple repos).
- **"Prisma is Active Record."** Closer to a repository — but without the entity-class step. The generated `prisma.user` is a typed repository.
- **"AR doesn't support DI."** It can, but it's awkward — you end up exporting the static-method module rather than injecting a service.
- **"DM is always heavier."** With good repository scaffolding (NestJS `@InjectRepository`, Spring `@Repository`), the boilerplate is minimal.
- **"You can't have transactions in AR."** Yes you can; but composing multiple AR saves in one TX requires passing a transaction object — exactly the DM pattern leaks in.

## Brute force approach

Use whichever the ORM defaults to. Works initially; pain comes when you need to test domain logic that touches the DB, or when an aggregate spans 3 tables.

## Optimal approach

1. **Pick by domain complexity**:
   - Simple CRUD, small team, ship fast → Active Record (Sequelize, Eloquent, Rails AR).
   - Complex domain, DDD, multiple aggregates → Repository / Data Mapper (Hibernate, SQLAlchemy, TypeORM Repository).
   - Modern Node, type-safety priority → Prisma's repository-like model.
2. **Mix is fine** — most codebases evolve; AR initially, repositories carved out for complex aggregates.
3. **Avoid TypeORM's dual mode** — pick one and stick with it across the codebase; otherwise team conventions drift.
4. **Inject repositories** (NestJS, Spring) — never static-method-only.
5. **Repository scope**: one repo per aggregate root, not per table.
6. **Custom queries**: named methods (`findActiveByOrg`) rather than passing query objects around.

## Solution

```typescript
// ============================================================
// Active Record style (Sequelize)
// ============================================================
class User extends Model {
  declare id: number;
  declare email: string;
  declare active: boolean;

  static async findActiveByOrg(orgId: number) {
    return User.findAll({ where: { active: true, orgId } });
  }
}
User.init({ /* schema */ }, { sequelize, modelName: 'User' });

// Usage
const users = await User.findActiveByOrg(42);
users[0].active = false;
await users[0].save();

// Pain points:
// - User.findActiveByOrg can't be mocked easily in unit tests.
// - User's class knows about `sequelize` (the connection).
// - Composing User + Order saves in one TX requires passing `transaction`:
await sequelize.transaction(async (t) => {
  await user.save({ transaction: t });
  await order.save({ transaction: t });
});

// ============================================================
// Repository style (NestJS + TypeORM)
// ============================================================
@Entity()
class User {
  @PrimaryGeneratedColumn() id!: number;
  @Column() email!: string;
  @Column() active!: boolean;
}

@Injectable()
class UserRepository {
  constructor(@InjectRepository(User) private repo: Repository<User>) {}

  findById(id: number) { return this.repo.findOneByOrFail({ id }); }
  findActiveByOrg(orgId: number) { return this.repo.find({ where: { active: true, orgId } }); }
  save(u: User | User[]) { return this.repo.save(u); }
  delete(id: number) { return this.repo.delete({ id }); }
}

@Injectable()
class UserService {
  constructor(
    private users: UserRepository,
    private orders: OrderRepository,
    private ds: DataSource,
  ) {}

  async deactivateUser(id: number) {
    return this.ds.transaction(async (mgr) => {
      const u = await mgr.findOneByOrFail(User, { id });
      u.active = false;
      await mgr.save(u);
      await mgr.update(Order, { userId: id, status: 'PENDING' }, { status: 'CANCELLED' });
    });
  }
}

// Tests
describe('UserService', () => {
  it('deactivates user', async () => {
    const users = { findById: jest.fn(), save: jest.fn() } as any;
    // ... mock and assert
  });
});

// ============================================================
// Hibernate (Spring) — Repository pattern via Spring Data JPA
// ============================================================
public interface UserRepository extends JpaRepository<User, Long> {
  List<User> findByActiveTrueAndOrgId(Long orgId);
}

@Service
class UserService {
  @Autowired UserRepository users;
  @Autowired OrderRepository orders;

  @Transactional
  public void deactivate(Long id) {
    User u = users.findById(id).orElseThrow();
    u.setActive(false);
    orders.cancelPending(id);
  }
}
```

## Step-by-step dry run

### Use case: deactivate user; cancel pending orders.

#### Active Record:
```typescript
async function deactivate(id: number) {
  return sequelize.transaction(async (t) => {
    const u = await User.findByPk(id, { transaction: t });
    if (!u) throw new NotFoundError();
    u.active = false;
    await u.save({ transaction: t });
    await Order.update(
      { status: 'CANCELLED' },
      { where: { userId: id, status: 'PENDING' }, transaction: t }
    );
  });
}
```
- Coupled to model classes directly.
- Testing: must stub `User.findByPk` and `Order.update` — global classes; awkward.
- Transaction passed manually through every call.

#### Repository:
```typescript
async function deactivate(id: number) {
  return ds.transaction(async (mgr) => {
    const u = await mgr.findOneByOrFail(User, { id });
    u.active = false;
    await mgr.save(u);
    await mgr.update(Order, { userId: id, status: 'PENDING' }, { status: 'CANCELLED' });
  });
}
```
- Service depends on `DataSource` (injectable).
- Testing: stub a `DataSource` mock; test the orchestration.
- TX scope clean.

### Use case: write a unit test for the deactivation logic.

#### AR — gross:
```typescript
// Have to stub static methods on User, Order
jest.spyOn(User, 'findByPk').mockResolvedValue(fakeUser);
jest.spyOn(Order, 'update').mockResolvedValue([1]);
jest.spyOn(sequelize, 'transaction').mockImplementation(async (fn) => fn({} as any));
// ... and assert via these mocks
```

#### Repository — clean:
```typescript
const users = { findById: jest.fn().mockResolvedValue(fakeUser), save: jest.fn() };
const orders = { cancelPending: jest.fn() };
const service = new UserService(users as any, orders as any, mockDs);
await service.deactivate(1);
expect(users.save).toHaveBeenCalled();
expect(orders.cancelPending).toHaveBeenCalledWith(1);
```

DM wins on testability whenever the domain has nontrivial orchestration.

## How to think aloud in the interview

> "Active Record and Data Mapper are the two main ORM architectural patterns. The choice shapes everything:
>
> - **Active Record** — entity has `save()`, `find()`, etc. Sequelize, Rails AR, Eloquent. Strength: minimal boilerplate, fast for CRUD. Weakness: domain object knows about persistence — hard to test, hard to evolve when the domain gets complex.
>
> - **Data Mapper / Repository** — entity is pure; a separate repository persists it. Hibernate, SQLAlchemy, TypeORM Repository, Doctrine. Strength: testable, domain-pure, supports DDD aggregates. Weakness: more files, steeper learning curve.
>
> - **Prisma** is repository-like by design — `prisma.user.findUnique()` is a generated typed repo, with no entity class step.
>
> I'd pick:
> - Active Record for prototypes, simple CRUD-heavy apps, small teams.
> - Data Mapper when the domain has invariants, aggregates, or when testability matters (financial software, anything regulated).
> - Both can coexist — start with AR, carve repos out where the domain matters.
>
> Watch-outs:
> - TypeORM lets you do both; pick one team-wide.
> - Static class methods in AR are hard to mock; prefer DI.
> - One repo per aggregate root, not per table.
> - Naming: `findActiveByOrg()` beats passing query objects."

## Important takeaways

- Active Record: entity has its own persistence methods; simple, coupled.
- Data Mapper / Repository: pure entity + separate persister; testable, decoupled.
- Pick by domain complexity, not by hype.
- Active Record's testing is awkward because of global statics.
- Repository pattern enables DI, mock-friendly tests, DDD aggregates.
- Prisma is repository-like without entity classes.
- TypeORM supports both styles — pick one and stick with it.

## Variants

1. **CQRS** — read side via raw SQL / DTOs, write side via repositories.
2. **Generic repositories vs specific** — `Repository<User>` vs `UserRepository extends Repository<User>` with custom finders.
3. **Specification pattern** — `UserSpec.activeIn(org)` returns a query builder; repository accepts specs. Powerful but heavy.
4. **CRUD via API service** — repositories wrapped in an HTTP service for cross-process domain.
5. **Repository per aggregate** (DDD) — not per table; the repo persists the whole aggregate as one unit.
6. **Service layer is the boundary** — repositories never crossed by controllers directly.
7. **Hybrid** — start with AR, migrate hot paths to repos; both can live in the same codebase.

## Revision notes

> **repository-vs-active-record — 60 second recap**
> - AR: entity has save/find; Sequelize, Rails AR, Eloquent. Fast to ship; coupled domain.
> - DM / Repository: pure entity + separate persister; Hibernate, SQLAlchemy, TypeORM repo. Testable; more files.
> - Prisma = generated repository without entity class.
> - Pick by domain complexity, not by hype.
> - One repo per aggregate root, not per table.
> - TypeORM supports both; pick one team-wide.
> - AR static methods are hard to mock; prefer DI everywhere.
> - CQRS: write through repo, read through raw SQL / DTO.
